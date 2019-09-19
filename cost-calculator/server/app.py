import logging
import functools
from server.instance_selector import make_instance_selector
from flask import Flask, request, jsonify
import flask

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
app = Flask(__name__)

instance_selectors = {}


@app.before_first_request
def setup():
    global instance_selector
    instance_selectors['aws'] = make_instance_selector('aws')
    instance_selectors['azure'] = make_instance_selector('azure')


def handle_exception(e, *args, **kwargs):
    error_message = 'Error processing request. ' + str(e)
    kwargs['error_message'] = error_message
    return flask.render_template('error.html', **kwargs)


def catch_errors(func):
    '''
    Wraps the handler in a try/except and shows an error page if
    there's an exception. Highlights the correct page in the sidebar
    but assumes the handler function name matches the expected
    active_page template value.  You know what happens when you
    assume, it makes... the code concise! Totally. Thats it. This'll
    never break.
    '''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return handle_exception(e, active_page=func.__name__)
    return wrapper


def to_float(v):
    try:
        return float(v)
    except Exception:
        return 0.0


# @catch_errors
def tester():
    return flask.render_template('tester.html')


@app.route('/')
def questionnaire():
    return flask.render_template('calculator.html')


def get_percent(v):
    v = to_float(v)
    if v > 1.0:
        v *= 0.01
    return v


def comparison_chart_json(workload_names, aws_data, azure_data):
    return {
        "type": 'bar',
        "data": {
            'labels': workload_names,
            'datasets': [
                {
                    'label': 'AWS',
                    'data': aws_data,
                    'backgroundColor': '#ff9900',
                    'borderColor': '#ff9900',
                    'borderWidth': 1
                },
                {
                    'label': 'Azure',
                    'data': azure_data,
                    'backgroundColor': '#007fff',
                    'borderColor': '#007fff',
                    'borderWidth': 1,
                },
            ]
        },
        'options': {
            'scales': {
                'yAxes': [{
                    'ticks': {'beginAtZero': True}
                }]
            },
            'legend': {'display': True}
        }
    }


def create_comparison(cloud, region, input_data, workload_costs):
    workload_names = [d['workloadName'] for d in workload_costs]
    if cloud == 'aws':
        aws_costs = workload_costs
        azure_region = 'Central US'
        azure_costs, _ = compute_single_cloud_costs(
            'azure', azure_region, input_data)
    else:
        azure_costs = workload_costs
        aws_region = 'us-east-1'
        aws_costs, _ = compute_single_cloud_costs(
            'aws', aws_region, input_data)
    aws_data = [round(d['monthlyCost'], 2) for d in aws_costs]
    azure_data = [round(d['monthlyCost'], 2) for d in azure_costs]
    return comparison_chart_json(workload_names, aws_data, azure_data)


def compute_single_cloud_costs(cloud, region, data):
    inst_sel = instance_selectors[cloud]
    costs = []
    total_monthly_cost = 0
    for i, item in enumerate(data['items']):
        cpu = to_float(item['cpu'])
        memory = to_float(item['memory'])
        block_storage = to_float(item['blockStorage'])
        quantity = to_float(item['quantity'])
        utilization = get_percent(item['utilization'])
        workload_name = item['workloadName'] or 'Workload {}'.format(i + 1)
        instance_type, instance_hourly_cost = inst_sel.get_cheapest_instance(
            cpu, memory, region)
        storage_hourly_cost = inst_sel.get_storage_price(region, block_storage)
        workload_hourly_cost = (utilization * quantity *
                                (instance_hourly_cost + storage_hourly_cost))
        total_monthly_cost += workload_hourly_cost * 720
        costs.append({
            'workloadName': workload_name,
            'instanceType': instance_type,
            'instanceHourlyCost': instance_hourly_cost,
            'storageCost': storage_hourly_cost,
            'monthlyCost': workload_hourly_cost * 720,
        })
    return costs, total_monthly_cost


# input data:
# items = [
# {workloadName: '', quantity: 1, cpu: 1, memory: 1, blockStorage: 0},
# ...
# ]
#
# output:
# {
#     summary: {hourlyCost},
#     items: [{workloadName, instanceType, hourlyCost}...],
# }
#
@app.route('/cost', methods=['POST'])
def get_cost():
    data = request.get_json()
    print(data)
    cloud = data['cloud']
    region = data['region']
    workload_costs, workload_total = compute_single_cloud_costs(cloud, region, data)
    comparison_chart = create_comparison(
        cloud, region, data, workload_costs)
    response = {
        'monthlyCost': workload_total,
        'details': workload_costs,
        'costComparisonChart': comparison_chart
    }
    print(response)
    return jsonify(response)
