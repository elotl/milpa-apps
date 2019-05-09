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
    def __init__(self, inst_datas_regions):
        self.inst_datas_regions = inst_datas_regions

    def price_for_cpu_spec(self, cpu, inst):
        if not inst['burstable']:
            return inst['price']
        elif cpu < inst['baseline']:
            return inst['price']
        else:
            cpu_needed = cpu - inst['baseline']
            extra_cpu_cost = cpu_needed * t_unlimited_price
            cost = inst['price'] + extra_cpu_cost
            return cost

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
            price = self.price_for_cpu_spec(cpu_request, inst)
            if price > 0.0 and price < lowest_price:
                lowest_price = price
                cheapest_instance = inst['instanceType']
        return cheapest_instance, lowest_price



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


def make_instance_selector():
    # read in files
    files = [
        'aws_instance_data.json',
    ]
    for f in files:
        url = 'https://s3.amazonaws.com/elotl-cloud-data/' + f
        download_file_if_not_exists(url)
    instancejson = open(datadir + '/aws_instance_data.json').read()
    instancedict = json.loads(instancejson)
    return InstanceSelector(instancedict)


def tests():
    region = 'us-east-1'
    instance_selector = make_instance_selector()
    print(instance_selector.get_cheapest_instance(1, 1, region))
    print(instance_selector.get_cheapest_instance(1, 8, region))
    print(instance_selector.get_cheapest_instance(.8, 8, region))
    print(instance_selector.get_cheapest_instance(.9, 8, region))
    print(instance_selector.get_cheapest_instance(2, 8, region))
    print(instance_selector.get_cheapest_instance(0, 0, region))


def main():
    tests()


if __name__ == '__main__':
    main()
