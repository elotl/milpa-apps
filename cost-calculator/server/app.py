import logging
import functools
from server.instance_selector import make_instance_selector
from flask import Flask, request
import flask

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
app = Flask(__name__)

instance_selector = None


@app.before_first_request
def setup():
    global instance_selector
    instance_selector = make_instance_selector


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


@app.route('/')
#@catch_errors
def questionnaire():
    return flask.render_template('questionnaire.html')


@app.route('/cost')
def get_cost():
    data = request.get_json()
    return flask.render_template('costq.html')
    # go through and use the instance selector to calculate
    # price and
