import json
import datetime

from dateutil.parser import parse

from dashboard.util import dpath


def nested_cls(cls, d):
    if d is None:
        return None
    return cls(d)


# if our datestr is None then it's a deletionTimestamp
# and the usage should be considered ended now
def to_date_attr(datestr):
    if datestr is None:
        return datetime.datetime.now()
    else:
        dt = parse(datestr)
        if dt.tzinfo is not None:
            # convert to UTC, non TZ aware date
            dt = datetime.datetime(*dt.utctimetuple()[:6])
        return dt


class Usage(object):
    def __init__(self, d):
        self.apiVersion = dpath(d, 'apiVersion')
        self.kind = dpath(d, 'kind')
        self.creation_timestamp = to_date_attr(
            dpath(d, 'metadata', 'creationTimestamp'))
        self.deletion_timestamp = to_date_attr(
            dpath(d, 'metadata', 'deletionTimestamp'))
        self.labels = dpath(d, 'metadata', 'labels', default={})
        self.instance = nested_cls(Instance, d.get('instance'))
        self.storage = nested_cls(Storage, d.get('storage'))
        self.network = nested_cls(Network, d.get('network'))
        self.peripheral = nested_cls(Peripheral, d.get('peripheral'))

    def __repr__(self):
        return '<Usage: {} - {}, instance:{}|storage:{}|network:{}|peripheral:{}>'.format(
            self.creation_timestamp,
            self.deletion_timestamp,
            self.instance, self.storage, self.network, self.peripheral)
        # return '<Usage: metadata:{}|instance:{}|storage:{}|network:{}|peripheral:{}>'.format(
        #     self.metadata, self.instance, self.storage, self.network, self.peripheral)


# class Metadata(object):
#     def __init__(self, d):
#         self.creation_timestamp = to_date_attr(d.get('creationTimestamp'))
#         self.deletion_timestamp = to_date_attr(d.get('deletionTimestamp'))
#         self.labels = d.get('labels', {})

#     def __repr__(self):
#         return '<Metadata: creation_timestamp:{}|deletion_timestamp:{}|labels:{}>'.format(
#             self.creation_timestamp, self.deletion_timestamp, self.labels)


class Instance(object):
    def __init__(self, d):
        self.instance_type = dpath(d, 'type')
        self.spot = dpath(d, 'spot')

    def __repr__(self):
        return '<Instance: instance_type:{}|spot:{}>'.format(
            self.instance_type, self.spot)


class Storage(object):
    def __init__(self, d):
        self.storage_type = dpath(d, 'type')
        self.size = dpath(d, 'size')

    def __repr__(self):
        return '<Storage: storage_type:{}|size:{}>'.format(
            self.storage_type, self.size)


class Network(object):
    def __init__(self, d):
        self.network_type = dpath(d, 'type')
        self.count = dpath(d, 'count')

    def __repr__(self):
        return '<Network: network_type:{}|count:{}>'.format(
            self.network_type, self.count)


class Peripheral(object):
    def __init__(self, d):
        self.name = dpath(d, 'name')
        self.count = dpath(d, 'count')

    def __repr__(self):
        return '<Peripheral: name:{}|count:{}>'.format(
            self.storage_type, self.size)


# usagejson = """    {
#         "apiVersion": "v1",
#         "instance": {
#             "spot": false,
#             "type": "t3.micro"
#         },
#         "kind": "Usage",
#         "metadata": {
#             "creationTimestamp": "2018-10-09T21:31:48.246603611Z",
#             "deletionTimestamp": "2018-10-09T21:51:20.350662542Z",
#             "labels": {
#                 "app": "milpasite"
#             },
#             "name": "12cef8c5-349f-4986-bfe1-9e57c8a5b171",
#             "namespace": "default",
#             "uid": "4d8d70ad-eca4-4ffe-942c-9f5d5b6afcfa"
#         },
#         "storage": {
#             "size": 2,
#             "type": "gp2"
#         }
#     }
# """
# usagedict = json.loads(usagejson)
# use = MyUsage(usagedict)
# print(use)
