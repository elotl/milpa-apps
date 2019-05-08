import json
import time


class CostCalculator(object):
    def __init__(self, region, instancejson, storagejson, networkjson):
        self.instance_lookup = self._instancejson_to_cost(region, instancejson)
        self.storage_lookup = json.loads(storagejson)[region]
        self.network_lookup = json.loads(networkjson)[region]

    def _instancejson_to_cost(self, region, instancejson):
        vals = json.loads(instancejson)[region]
        instance_lookup = {}
        for v in vals:
            itype = v['instanceType']
            instance_lookup[itype] = v['price']
        return instance_lookup

    def instance_cost(self, instance_type, hours):
        return self.instance_lookup[instance_type] * hours

    def storage_cost(self, storage_type, size, hours):
        return self.storage_lookup[storage_type]['price'] * size * hours

    def network_cost(self, network_type, count, hours):
        return self.network_lookup[network_type]['price'] * count * hours
