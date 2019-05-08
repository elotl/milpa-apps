import json
import os
import shlex
import subprocess

from dashboard.milpatypes import to_types


class Milpactl(object):
    def __init__(self, default_path='/milpactl/milpactl', default_endpoint='milpa', default_port='54555'):
        milpactl_path = os.environ.get('MILPACTL', default_path)
        if not os.path.isfile(milpactl_path):
            msg = ("""
Could not find milpactl at {}. Please set MILPACTL environment variable to the location of milpactl on the filesystem.
For example:
MILPACTL=/opt/milpa/bin/milpactl
When running on milpa, the path will depend on the path of the mounted volume containing milpactl and certificates.""").format(milpactl_path)
            raise Exception(msg)
        api_endpoint = os.environ.get('MILPA_ENDPOINT', default_endpoint)
        api_port = os.environ.get('MILPA_API_PORT', default_port)
        self.basecmd = "{} --endpoints {}:{}".format(
            milpactl_path, api_endpoint, api_port)

    def __call__(self, cmd, raw=False):
        cmdparts = [self.basecmd]
        if raw is False:
            cmdparts.append('-ojson')
        cmdparts.append(cmd)
        fullcmd = ' '.join(cmdparts)
        output = subprocess.check_output(
            shlex.split(fullcmd), stderr=subprocess.STDOUT)
        if raw:
            return output
        pydict = json.loads(output.decode('utf-8'))
        return to_types(pydict)
