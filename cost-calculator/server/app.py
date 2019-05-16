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
    response_details = []
    total_hourly_cost = 0
    cloud = data['cloud']
    inst_sel = instance_selectors[cloud]
    region = data['region']
    for i, item in enumerate(data['items']):
        cpu = to_float(item['cpu'])
        memory = to_float(item['memory'])
        block_storage = to_float(item['blockStorage'])
        quantity = to_float(item['quantity'])
        workload_name = item['workloadName'] or 'Workload {}'.format(i + 1)
        instance_type, instance_hourly_cost = inst_sel.get_cheapest_instance(
            cpu, memory, region)
        storage_hourly_cost = inst_sel.get_storage_price(
            region, block_storage)
        workload_storage_cost = quantity * storage_hourly_cost
        workload_hourly_cost = ((quantity * instance_hourly_cost)
                                + workload_storage_cost)
        total_hourly_cost += workload_hourly_cost
        response_details.append({
            'workloadName': workload_name,
            'instanceType': instance_type,
            'instanceHourlyCost': instance_hourly_cost,
            'storageCost': workload_storage_cost,
            'hourlyCost': workload_hourly_cost,
        })
    response = {
        'hourlyCost': total_hourly_cost,
        'details': response_details,
    }
    print(response)
    return jsonify(response)
