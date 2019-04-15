import re
import os
import logging
import datetime
import subprocess
import shutil
import functools
import tempfile

from flask import Flask, request
import flask
import dateutil.relativedelta
from dateutil.parser import parse
import requests

from dashboard.usage import Usage
from dashboard.cost_calculator import CostCalculator
from dashboard.cost_bucket import Chart as ChartData
from dashboard.util import dpath
from dashboard.milpactl import Milpactl
import dashboard.charts as charts

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
app = Flask(__name__)

POD_TERMINATED = 'Terminated'
DATE_FMT = "%Y-%m-%d"
datadir = os.environ.get('DATA_DIR', '/tmp')
if os.environ.get('FLASK_ENV', '') == 'development':
    milpactl = Milpactl('/opt/milpa/bin/milpactl', 'localhost')
else:
    milpactl = Milpactl()
# cc is our cost_calculator and it must be initialized in
# before_first_request
cc = None


def get_age(created_at):
    now = datetime.datetime.now()
    if created_at.tzinfo is not None:
        now = now.replace(tzinfo=created_at.tzinfo)
    age = now - created_at
    if age.days > 0:
        return str(age.days) + 'd'
    s = age.seconds
    if s // 3600 > 0:
        return str(s//3600) + 'h'
    if s // 60 > 0:
        return str(s//60) + 'm'
    if s > 0:
        return str(s) + 's'
    return '0s'


def get_address_helper(addresses, address_type):
    for a in addresses:
        if a.get('type') == address_type:
            return a.get('address')
    return 'n/a'


def get_public_ip(addresses):
    return get_address_helper(addresses, 'PublicIP')


def get_private_ip(addresses):
    return get_address_helper(addresses, 'PrivateIP')


def make_port_string(ports):
    pieces = []
    for port in ports:
        portnum = port['port']
        rangesize = port.get('portRangeSize', 1)
        proto = port.get('protocol', 1)
        if rangesize > 1:
            s = '{}-{}/{}'.format(portnum, portnum+rangesize, proto)
        else:
            s = '{}/{}'.format(portnum, proto)
        pieces.append(s)
    return ','.join(pieces)


def embellish_pods(pods):
    def embellish_pod(pod):
        try:
            status = pod['status'].get('phase', 'Waiting')
            reason = ''
            restarts = 0
            running_units = 0
            for unitStatus in dpath(pod, 'status', 'unitStatuses', default=[]):
                restarts += unitStatus.get('restartCount', 0)
                if dpath(unitStatus, 'state', 'waiting') is not None:
                    unit_reason = dpath(
                        unitStatus, 'state', 'waiting', 'reason', default='')
                    reason = 'Unit Waiting: ' + unit_reason
                elif dpath('unit', 'state', 'terminated') is not None:
                    exit_code = dpath(
                        unitStatus, 'state', 'terminated', 'exitCode', default=0)
                    reason = 'Unit Terminated: ExitCode: ' + exit_code
                elif dpath(unitStatus, 'state', 'running') is not None:
                    running_units += 1
            if reason != '':
                status += ' - ' + reason
            pod['running_units'] = running_units
            pod['status_summary'] = status
            pod['restarts'] = restarts
        except Exception:
            pass
        return pod

    pods = [embellish_pod(p) for p in pods]
    return pods


def embellish_services(svcs):
    for svc in svcs:
        try:
            if dpath(svc, 'spec', 'type') == 'LoadBalancer':
                ingresses = dpath(
                    svc, 'status', 'loadBalancer', 'ingress', default=[])
                if len(ingresses) > 0:
                    svc['ingress'] = ingresses[0].get('hostname', '')

            svc['portstring'] = make_port_string(
                dpath(svc, 'spec', 'ports', default=[]))
            svc['source_ranges_string'] = ','.join(
                dpath(svc, 'spec', 'sourceRanges', default=[]))
        except Exception:
            pass
    return svcs


def embellish_nodes(nodes):
    for node in nodes:
        try:
            itype = node['spec'].get('instance_type', '')
            if dpath(node, 'spec', 'spot', default=False):
                itype += ' (spot)'
            node['instance_type'] = itype
            ip = get_public_ip(node['status'].get('addresses', []))
            if not ip:
                ip = get_private_ip(node['status'].get('addresses', []))
            node['ip'] = ip
        except Exception:
            pass
    return nodes


def embellish_with_age(objs):
    for obj in objs:
        try:
            dt = parse(obj['metadata']['creationTimestamp'])
            obj['age'] = get_age(dt)
        except Exception as e:
            print('Error calculating age:', e)
            continue
    return objs


def get_quarter_start(d):
    q = d.month // 4
    return datetime.datetime(d.year, q*3+1, 1)


def date_to_datetime(d):
    return datetime.datetime.fromordinal(d.toordinal())


def format_currency(value):
    '''
    We could use: locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') but
    sadly setting up locales in Alpine is more work than its worth...
    '''
    return '${:,.2f}'.format(value)


def get_usage(start, end, selector=None):
    startstr = start.strftime(DATE_FMT)
    endstr = end.strftime(DATE_FMT)
    cmd = 'usage --raw --start-date {} --end-date {}'.format(
        startstr, endstr)
    if selector:
        cmd += " --selector '{}'".format(selector)
    usage = milpactl(cmd)
    usage_records = [Usage(d) for d in usage]
    return usage_records


def make_chart(usage_records, start, end, resolution, chart_type, group_by):
    chart = ChartData(start, end, resolution, cc)
    chart.add_usage(usage_records)
    xvals = chart.xvals()
    if group_by == 'none':
        yvals = chart.total_cost()
        yval_names = ['Total Cost']
    elif group_by == 'category':
        yval_names, yvals = chart.category_costs()
    elif group_by == 'type':
        yval_names, yvals = chart.specific_type_costs()
    if chart_type == 'doughnut':
        return charts.make_donut_chart(xvals, yvals, yval_names)
    else:
        return charts.make_standard_chart(xvals, yvals, yval_names, chart_type)


def get_cost(usage_records, start, end):
    chart = ChartData(start, end, 'none', cc)
    chart.add_usage(usage_records)
    total = chart.total_cost()[0][0]
    return total


def get_msg_from_exception(e):
    msg = 'Error processing request. '
    if type(e) == subprocess.CalledProcessError:
        output = e.output.decode("utf-8").strip()
        print(output)
        msg += ('could not get usage from milpactl: '
                'return code: {}. Output: {}').format(e.returncode, output)
    else:
        msg += str(e)
    return msg


def illegal_selector_msg(selector):
    '''
    We don't shell out to milpactl but security comes in layers. Lets
    go ahead and sanitize our inputs.
    '''
    selector_chars = r'[a-zA-Z0-9()._\-/=!, ]'
    bad_chars = set()
    for c in selector:
        if not re.match(selector_chars, c):
            bad_chars.add(c)
    if bad_chars:
        charstr = ', '.join(bad_chars)
        return "Bad characters in filter labels: " + charstr


# Todo: consider packaging pricing data into the container for
# environemnts without internet access. Use an env var to copy
# data from there
@app.before_first_request
def setup_cost_calculator():
    global cc
    files = [
        'aws_instance_data.json',
        'aws_storage_data.json',
        'aws_network_data.json'
    ]
    for f in files:
        url = 'https://s3.amazonaws.com/elotl-cloud-data/' + f
        download_file_if_not_exists(url)
    instancejson = open(datadir + '/aws_instance_data.json').read()
    storagejson = open(datadir + '/aws_storage_data.json').read()
    networkjson = open(datadir + '/aws_network_data.json').read()
    cc = CostCalculator('us-east-2', instancejson, storagejson, networkjson)


def download_file_if_not_exists(url):
    '''
    Downloads json procing files to the local filesystem. We could
    have multiple processes running so to combat collisions, we'll
    download to a random filename and then rename the file cause that
    should be atomic.
    '''
    local_filename = url.split('/')[-1]
    filepath = os.path.join(datadir, local_filename)
    if not os.path.exists(filepath):
        print('downloading', url)
        r = requests.get(url, stream=True)
        _, tmppath = tempfile.mkstemp(prefix=local_filename, dir=datadir)
        with open(tmppath, 'wb') as fp:
            shutil.copyfileobj(r.raw, fp)
        os.rename(tmppath, filepath)


def handle_exception(e, *args, **kwargs):
    error_message = get_msg_from_exception(e)
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


############################################################
# routes
############################################################
@app.route('/')
@catch_errors
def overview():
    today = datetime.datetime.now()
    tomorrow = today.date() + datetime.timedelta(days=1)
    eod = date_to_datetime(tomorrow)
    first_of_month = datetime.datetime(today.year, today.month, 1)
    monthly_chart_start = (
        first_of_month - dateutil.relativedelta.relativedelta(months=2))
    quarter_start = get_quarter_start(today)
    usage_start = min(monthly_chart_start, quarter_start)
    month_details_link = (
        'details?resolution=daily&chartType=stacked&groupBy=category&'
        'startDate={}&endDate={}').format(
            first_of_month.strftime(DATE_FMT), today.strftime(DATE_FMT))
    quarter_details_link = (
        'details?resolution=weekly&chartType=stacked&groupBy=category&'
        'startDate={}&endDate={}').format(
            quarter_start.strftime(DATE_FMT), today.strftime(DATE_FMT))
    usage_records = get_usage(usage_start, eod)
    month_to_date_cost = get_cost(usage_records, first_of_month, eod)
    quarter_to_date_cost = get_cost(usage_records, quarter_start, eod)

    monthly_chart = make_chart(usage_records, monthly_chart_start, eod,
                               'monthly', 'bar', 'none')
    category_chart = make_chart(usage_records, first_of_month, eod,
                                'none', 'doughnut', 'category')
    return flask.render_template(
        'overview.html',
        month_details_link=month_details_link,
        quarter_details_link=quarter_details_link,
        month_to_date_cost=format_currency(month_to_date_cost),
        quarter_to_date_cost=format_currency(quarter_to_date_cost),
        monthly_chart=monthly_chart,
        category_chart=category_chart)


@app.route('/details')
def details():
    default_resolution = 'weekly'
    default_chart_type = 'bar'
    default_group_by = 'none'
    today = datetime.datetime.now()
    today_str = today.strftime(DATE_FMT)
    month_ago = today - dateutil.relativedelta.relativedelta(months=1)
    month_ago_str = month_ago.strftime(DATE_FMT)
    startstr = request.args.get(
        'startDate',
        request.cookies.get('details_start_date', month_ago_str))
    start = datetime.datetime.strptime(startstr, DATE_FMT)
    endstr = request.args.get(
        'endDate',
        request.cookies.get('details_end_date', today_str))
    end = datetime.datetime.strptime(endstr, DATE_FMT)
    # make our end date inclusive of that day
    day_after_end = end + datetime.timedelta(days=1)
    eod = day_after_end - datetime.timedelta(microseconds=1)
    resolution = request.args.get('resolution', default_resolution)
    chart_type = request.args.get(
        'chartType',
        request.cookies.get('details_chart_type', default_chart_type))
    group_by = request.args.get(
        'groupBy',
        request.cookies.get('details_group_by', default_group_by))
    selector = request.args.get(
        'selector',
        request.cookies.get('details_selector', ''))
    error_message = illegal_selector_msg(selector)
    if error_message:
        selector = ''
    try:
        usage_records = get_usage(start, day_after_end, selector)
    except Exception as e:
        error_message = get_msg_from_exception(e)
        # we likely had a bad selector but maybe something else, For
        # now, reset the chart settings.
        resp = flask.make_response(
            flask.render_template(
                'details.html',
                main_chart={'type': 'bar'},
                resolution=default_resolution,
                chart_type=default_chart_type,
                group_by=default_group_by,
                start_date=month_ago.date(),
                end_date=today.date(),
                error_message=error_message,
            )
        )
        resp.set_cookie('details_start_date', month_ago_str)
        resp.set_cookie('details_end_date', today_str)
        resp.set_cookie('details_chart_type', default_chart_type)
        resp.set_cookie('details_group_by', default_group_by)
        return resp

    main_chart = make_chart(usage_records, start, eod,
                            resolution, chart_type, group_by)
    resp = flask.make_response(
        flask.render_template(
            'details.html',
            main_chart=main_chart,
            resolution=resolution,
            chart_type=chart_type,
            group_by=group_by,
            start_date=start.date(),
            end_date=end.date(),
            selector=selector,
            error_message=error_message,
        )
    )
    resp.set_cookie('details_start_date', startstr)
    resp.set_cookie('details_end_date', endstr)
    resp.set_cookie('details_chart_type', chart_type)
    resp.set_cookie('details_group_by', group_by)
    resp.set_cookie('details_selector', selector)
    return resp


@app.route('/pods')
@catch_errors
def pods():
    pods = milpactl('get po')
    pods = embellish_pods(pods)
    pods = embellish_with_age(pods)
    pods = [pod for pod in pods
            if pod['status']['phase'] != POD_TERMINATED]
    return flask.render_template('pods.html', pods=pods)


@app.route('/deployments')
@catch_errors
def deployments():
    deploys = milpactl('get deploy')
    deploys = embellish_with_age(deploys)
    return flask.render_template('deployments.html', deployments=deploys)


@app.route('/replicasets')
@catch_errors
def replicasets():
    rss = milpactl('get rs')
    rss = embellish_with_age(rss)
    return flask.render_template('replicasets.html', replicasets=rss)


@app.route('/services')
@catch_errors
def services():
    svcs = milpactl('get svc')
    svcs = embellish_services(svcs)
    svcs = embellish_with_age(svcs)
    return flask.render_template('services.html', services=svcs)


@app.route('/nodes')
@catch_errors
def nodes():
    nodes = milpactl('get nodes')
    nodes = embellish_nodes(nodes)
    nodes = embellish_with_age(nodes)
    return flask.render_template('nodes.html', nodes=nodes)
