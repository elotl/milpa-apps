import os
import tempfile
import shutil
import json

import requests
# load instance data for aws and azure
#

t_unlimited_price = 0.05
datadir = os.environ.get('DATA_DIR', '/tmp')


class InstanceSelector(object):
    def __init__(self, cloud, inst_datas_regions, storage_by_region):
        self.cloud = cloud
        self.inst_datas_regions = inst_datas_regions
        self.storage_by_region = storage_by_region

    def price_for_cpu_spec(self, cpu, inst):
        if not inst['burstable']:
            return inst['price'], False
        elif cpu <= inst['baseline']:
            return inst['price'], False
        elif self.cloud == 'aws':
            cpu_needed = cpu - inst['baseline']
            extra_cpu_cost = cpu_needed * t_unlimited_price
            cost = inst['price'] + extra_cpu_cost
            return cost, True
        return -1, False

    def find_cheapest_instance(self, insts):
        lowest_price = 100000000.0
        cheapest_instance = ""
        for inst in insts:
            if inst['price'] > 0 and inst['price'] < lowest_price:
                lowest_price = inst['price']
                cheapest_instance = inst['instanceType']
        return cheapest_instance, lowest_price

    def get_cheapest_instance(self, cpu_request, memory_request, region):
        # load up initial data and start filtering things that
        # don't match
        matches = self.inst_datas_regions[region]
        matches = [inst for inst in matches
                   if (memory_request == 0.0 or
                       inst['memory'] >= memory_request)]
        matches = [inst for inst in matches
                   if (cpu_request == 0.0 or
                       inst['memory'] >= cpu_request)]
        cheapest_instance = ""
        lowest_price = 100000000.0
        # if resource_spec.dedicated_cpu:
        #     matches = [inst for inst in matches if not inst.burstable]
        #     cheapest_instance, lowest_price = self.find_cheapest_instance(
        #         matches)
        # else:
        for inst in matches:
            if inst['cpu'] < cpu_request:
                continue
            price, is_t_unlimited = self.price_for_cpu_spec(cpu_request, inst)
            if price > 0.0 and price < lowest_price:
                lowest_price = price
                cheapest_instance = inst['instanceType']
                if is_t_unlimited:
                    cheapest_instance += ' (unlimited)'
        return cheapest_instance, lowest_price

    def get_storage_price(self, region, quantity):
        '''
        this one is a little bit hackey but, due to azures interesting
        pricing model (buckets) and the fact that we already have a
        format for AWS storage pricing thats used in the dashboard,
        we're just going to choose the function based on the cloud
        :(
        '''
        def get_storage_price_aws():
            return self.storage_by_region[region]['gp2']['price'] * quantity

        def get_storage_price_azure():
            if quantity == 0:
                return 0.0
            region_offers = self.storage_by_region[region]['StandardSSD']
            for offer in region_offers:
                if offer['minSizeGiB'] < quantity <= offer['maxSizeGiB']:
                    return offer['price']
            raise Exception("Could not find price for storage")

        if self.cloud == 'aws':
            return get_storage_price_aws()
        else:
            return get_storage_price_azure()


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


def make_instance_selector(cloud):
    instance_fn = '{}_instance_data.json'.format(cloud)
    storage_fn = '{}_storage_data.json'.format(cloud)
    for f in [instance_fn, storage_fn]:
        url = 'https://s3.amazonaws.com/elotl-cloud-data/' + f
        download_file_if_not_exists(url)
    instancejson = open(os.path.join(datadir, instance_fn)).read()
    instancedict = json.loads(instancejson)
    storagejson = open(os.path.join(datadir, storage_fn)).read()
    storagedict = json.loads(storagejson)
    return InstanceSelector(cloud, instancedict, storagedict)


def tests():
    tests = [
        ('aws', 'us-east-1'),
        ('azure', 'East US 2'),
    ]
    for cloud, region in tests:
        instance_selector = make_instance_selector(cloud)
        print(instance_selector.get_cheapest_instance(1, 1, region))
        print(instance_selector.get_cheapest_instance(1, 8, region))
        print(instance_selector.get_cheapest_instance(.2, 1, region))
        print(instance_selector.get_cheapest_instance(.8, 8, region))
        print(instance_selector.get_cheapest_instance(.9, 8, region))
        print(instance_selector.get_cheapest_instance(2, 8, region))
        print(instance_selector.get_cheapest_instance(0, 0, region))
        print("Storage")
        print(instance_selector.get_storage_price(region, 0))
        print(instance_selector.get_storage_price(region, 1))
        print(instance_selector.get_storage_price(region, 32))
        print(instance_selector.get_storage_price(region, 35))


def main():
    tests()


if __name__ == '__main__':
    main()
