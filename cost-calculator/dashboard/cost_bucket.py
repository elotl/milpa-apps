import math
from collections import defaultdict, OrderedDict
import datetime
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY

SECONDS_IN_AN_HOUR = 3600
monthly = 'monthly'
daily = 'daily'
weekly = 'weekly'


def moneyround(n):
    decimals = 2
    multiplier = 10 ** decimals
    return math.floor(n*multiplier + 0.5) / multiplier


class CostBucket(object):
    def __init__(self, start, end, cost_calculator):
        self.start = start
        self.end = end
        self.cost_calculator = cost_calculator
        self.items = 0
        self.total_cost = 0.0
        self.category_costs = defaultdict(float)
        self.specific_type_costs = defaultdict(float)

    def _add_cost(self, cost, category, specific_type):
        self.total_cost += cost
        self.category_costs[category] += cost
        self.specific_type_costs[specific_type] += cost

    def add_usage(self, usage):
        if (usage.creation_timestamp <= self.end and
                usage.deletion_timestamp > self.start):
            self.items += 1
            time_start = self.start
            if usage.creation_timestamp > self.start:
                time_start = usage.creation_timestamp
            time_end = self.end
            if usage.deletion_timestamp < self.end:
                time_end = usage.deletion_timestamp
            seconds = (time_end - time_start).total_seconds()
            hours = seconds / float(SECONDS_IN_AN_HOUR)
            if usage.instance is not None:
                t = usage.instance.instance_type
                cost = self.cost_calculator.instance_cost(t, hours)
                # print("Cost:", self.start, self.end, time_start, time_end, t, cost, hours, seconds)
                self._add_cost(cost, 'instances', t)
            if usage.storage is not None:
                t = usage.storage.storage_type
                cost = self.cost_calculator.storage_cost(
                    t, usage.storage.size, hours)
                self._add_cost(cost, 'storage', t)

            if usage.network is not None:
                t = usage.network.network_type
                cost = self.cost_calculator.network_cost(
                    t, usage.network.count, hours)
                self._add_cost(cost, 'network', t)
            if usage.peripheral is not None:
                t = usage.peripheral.name
                cost = self.cost_calculator.peripheral_cost(t, hours)
                self._add_cost(cost, 'peripheral', t)
            return True
        else:
            # print(usage.creation_timestamp, usage.deletion_timestamp)
            return False

    def __repr__(self):
        startstr = self.start.strftime('%Y%m%d')
        endstr = self.end.strftime('%Y%m%d')
        s = '<CostBucket: {} - {}, items: {}: total: {} c5-large> {}'.format(
            startstr, endstr, self.items, self.total_cost,
            self.specific_type_costs)
        return s


class Chart(object):
    def __init__(self, start, end, resolution, cost_calculator):
        self.resolution = resolution
        self.cost_calculator = cost_calculator
        self.buckets = self.create_buckets(start, end, resolution)

    def create_buckets(self, start, end, resolution):
        def month_window(start, end):
            all_dates = [datetime.datetime(d.year, d.month, 1) for d in
                         rrule(MONTHLY, dtstart=start, until=end)]
            return all_dates

        def day_window(start, end):
            all_dates = [datetime.datetime(d.year, d.month, d.day) for d in
                         rrule(DAILY, dtstart=start, until=end)]
            return all_dates

        def week_window(start, end):
            # move start to start of week
            start = start - datetime.timedelta(days=start.weekday())
            all_dates = [datetime.datetime(d.year, d.month, d.day) for d in
                         rrule(WEEKLY, dtstart=start, until=end)]
            return all_dates

        if resolution == monthly:
            all_dates = month_window(start, end)
        elif resolution == weekly:
            all_dates = week_window(start, end)
        elif resolution == daily:
            all_dates = day_window(start, end)
        elif resolution == 'none':
            all_dates = [start, end]
        else:
            raise Exception('Unknown period specified')

        # if start < all_dates[0]:
        # we had a problem when we computed weekly start dates. We really
        # need to compute these buckets from the requested start date
        all_dates[0] = start
        if end > all_dates[-1]:
            all_dates.append(end)

        buckets = []
        if len(all_dates) <= 2:
            bucket = CostBucket(start, end, self.cost_calculator)
            buckets.append(bucket)
        else:
            for i in range(len(all_dates)-1):
                bucket_start = all_dates[i]
                bucket_end = all_dates[i+1]
                bucket = CostBucket(
                    bucket_start, bucket_end, self.cost_calculator)
                buckets.append(bucket)
        return buckets

    def add_usage(self, usage):
        # this could be sped up if we sort usage and buckets
        for record in usage:
            for bucket in self.buckets:
                bucket.add_usage(record)

    def get_bucket_name(self, bucket):
        if self.resolution == 'monthly':
            return bucket.start.strftime('%b-%Y')
        else:
            return bucket.start.strftime('%b-%d-%y')

    def xvals(self):
        return [self.get_bucket_name(b) for b in self.buckets]

    def total_cost(self):
        vals = [moneyround(b.total_cost) for b in self.buckets]
        vals2d = [vals]
        return vals2d

    def category_costs(self):
        '''return a tuple of names and 2d values
        be careful to get the entire set of keys from our buckets
        or else we will miss datapoints.
        '''
        keys = set()
        for b in self.buckets:
            keys.update(b.category_costs.keys())

        sorted_keys = sorted(keys)
        aggregate = OrderedDict()
        for b in self.buckets:
            for category in sorted_keys:
                cost = b.category_costs[category]
                aggregate.setdefault(category, [])
                aggregate[category].append(moneyround(cost))
        return aggregate.keys(), aggregate.values()

    def specific_type_costs(self):
        '''return a tuple of names and 2d values
        be careful to get the entire set of keys from our buckets
        or else we will miss datapoints.
        '''
        keys = set()
        for b in self.buckets:
            keys.update(b.specific_type_costs.keys())
        sorted_keys = sorted(keys)
        aggregate = OrderedDict()
        for b in self.buckets:
            for specific_type in sorted_keys:
                cost = b.specific_type_costs[specific_type]
                aggregate.setdefault(specific_type, [])
                aggregate[specific_type].append(moneyround(cost))

        return aggregate.keys(), aggregate.values()


    def __repr__(self):
        s = ['<Chart']
        for b in self.buckets:
            s.append('  {}'.format(b))
        s.append('>')
        return '\n'.join(s)
