
"""
aggregates coins data by time intervals (specified in INTERVALS)

Data saved in separate collections:

    coins_1h
    coins_24h

Each entry in the collection has the following keys:

    "coin",
    "rank",
    "price_usd",
    "24h_volume_usd",
    "market_cap_usd",
    "available_supply",
    "total_supply",

all of that (except "coin"), in turn, has the following aggragated data:

    'min',
    'max',
    'begin',
    'end',
    'time_end',
    'time_min',
    'time_max'

The whole entry has additional fields:

    'timestamp',
    'number_of_aggregated'

Collections are indexed by coin and timestamp.

Example of an entry:

    > db.coins_1h.findOne()
    {
            "_id" : ObjectId("5abf7aed467767327a5a9f5e"),
            "market_cap_usd" : {
                    "begin" : 275907280960,
                    "time_max" : 1515364500,
                    "min" : 275907280960,
                    "max" : 279920325476,
                    "end" : 279074603826,
                    "time_min" : 1515363000,
                    "avg" : 278521868630.61536
            },
            "price_usd" : {
                    "begin" : 16434.4,
                    "time_max" : 1515364500,
                    "min" : 16434.4,
                    "max" : 16673.4,
                    "end" : 16623,
                    "time_min" : 1515363000,
                    "avg" : 16590.1
            },
            "24h_volume_usd" : {
                    "begin" : 15983300000,
                    "time_max" : 1515363300,
                    "min" : 15874100000,
                    "max" : 15989000000,
                    "end" : 15931000000,
                    "time_min" : 1515364800,
                    "avg" : 15945238461.538462
            },
            "timestamp" : 1515363000,
            "time_end" : 1515366600,
            "rank" : {
                    "begin" : 1,
                    "time_max" : 1515363000,
                    "min" : 1,
                    "max" : 1,
                    "end" : 1,
                    "time_min" : 1515363000,
                    "avg" : 1
            },
            "total_supply" : {
                    "begin" : 16788400,
                    "time_max" : 1515365700,
                    "min" : 16788400,
                    "max" : 16788462,
                    "end" : 16788462,
                    "time_min" : 1515363000,
                    "avg" : 16788438.153846152
            },
            "available_supply" : {
                    "begin" : 16788400,
                    "time_max" : 1515365700,
                    "min" : 16788400,
                    "max" : 16788462,
                    "end" : 16788462,
                    "time_min" : 1515363000,
                    "avg" : 16788438.153846152
            },
            "symbol" : "BTC"
    }

"""

import math

from mng import MongoReader, MongoWriter
MONGO_READER = MongoReader()
MONGO_WRITER = MongoWriter()
INTERVAL = {
    '1h':       1*3600,
}
#    '24h':      24*3600,

def _get_entries(coin, start_time, end_time):
    data = MONGO_READER.get_raw_data(coin, start_time, end_time)
    return data

def aggregate_coin(coin, time_start, interval):
    """
    Aggregate 5min _coin_ data starting from _start_time_
    for _interval_ (in seconds; must be divisible by 5m)
    and return aggregated information (dictionary).

    Fields of the result: min, max, avg, begin, end
    """

    time_end = time_start + interval
    entries = list(_get_entries(coin, time_start, time_end))

    keys = [
        "rank",
        "price_usd",
        "24h_volume_usd",
        "market_cap_usd",
        "available_supply",
        "total_supply",
    ]

    result = {
        'symbol': coin,
        'timestamp': entries[0].get('timestamp'),
        'time_end': entries[-1].get('timestamp'),
        'number_of_aggregated': len(entries),
    }

    for key in keys:

        aggregated = {
            'min':  entries[0].get(key),
            'max':  entries[0].get(key),
            'begin':entries[0].get(key),
            'end':  entries[-1].get(key),
            'time_min': entries[0].get('timestamp'),
            'time_max': entries[0].get('timestamp'),
        }

        sum_ = 0
        for entry in entries:
            this = entry.get(key)
            time_this = entry.get('timestamp')

            if this > aggregated['max']:
                aggregated['max'] = this
                aggregated['time_max'] = time_this

            if this < aggregated['min']:
                aggregated['min'] = this
                aggregated['time_min'] = time_this

            sum_ += this
        aggregated['avg'] = sum_/len(entries)

        result[key] = aggregated

    return result


def get_aggregated_coin(coin, time_start, time_end, number_of_ticks, key=None): # pylint: disable=too-many-locals
    """
    Highlevel reader that returns aggregated data ticks (based on agregated data)
    and agregated info about the data (min, max and so on).
    Data is returned in form:
    {
        'ticks': [...],
        'meta': {
            'min':,
            'max':,
            ...
        }
    }
    Number of ticks in the returned data can be greater than _number_of_ticks_
    """

    ticks = []
    meta = {}

    desired_interval = (time_end-time_start)/number_of_ticks

    chosen_interval = None
    for interval_name, interval_size in sorted(INTERVAL.items(), key=lambda x: -x[1]):
        if interval_size < desired_interval:
            chosen_interval = interval_name
    if chosen_interval:
        collection_name = 'coins_%s' % chosen_interval

    entries = MONGO_READER.get_raw_data(coin, time_start, time_end, collection_name=collection_name)

    if key is None:
        key = "price_usd"

    # this parameter should be take to the ticks
    take_this = 'avg'

    ticks = []
    meta = {
        'symbol': entries[0]['symbol'],
        'begin': entries[0][key]['begin'],
        'end': entries[-1][key]['end'],
        'time_begin': entries[0]['timestamp'],
        'time_end': entries[-1]['time_end'],

        'min': entries[0][key]['min'],
        'max': entries[0][key]['max'],
        'time_min': entries[0][key]['time_min'],
        'time_max': entries[0][key]['time_max'],
        }

    sum_ = 0
    for entry in entries:
        ticks.append(entry[key][take_this])
        sum_ += entry[key]['avg']

        if entry[key]['max'] > meta['max']:
            meta['max'] = entry[key]['max']
            meta['time_max'] = entry[key]['time_max']

        if entry[key]['min'] < meta['min']:
            meta['min'] = entry[key]['min']
            meta['time_min'] = entry[key]['time_min']

    meta['avg'] = sum_/len(ticks)

    return {
        'ticks': ticks,
        'meta': meta,
    }

def main():
    """
    Aggregator of existing entries
    """

    for coin in ['ETH']:

        first_timestamp = MONGO_READER.get_first_timestamp(coin)
        last_timestamp = MONGO_READER.get_first_timestamp(coin, last=True)

        for interval_name, interval_size in INTERVAL.items():
            collection_name = 'coins_' + interval_name

            last_aggregated_timestamp = \
                MONGO_READER.get_first_timestamp(coin, last=True, collection_name=collection_name)
            if last_aggregated_timestamp is None:
                print "[%s/%s] last_aggregated_timestamp is None" % (collection_name, coin)
                last_aggregated_timestamp = first_timestamp
            print "[%s/%s] %s entries to insert/update" % \
                (collection_name, coin,
                 int(math.ceil((last_timestamp - last_aggregated_timestamp)*1.0/interval_size)))
            #continue

            inserted_entries = 0
            timestamp = last_aggregated_timestamp
            while timestamp <= last_timestamp:
                entry = aggregate_coin(coin, timestamp, interval_size)
                # we insert all entries except the last one,
                # because it is possible that it is not yet completed
                # therefore we insert entry first, and calculate a new one thereafter
                if entry:
                    MONGO_WRITER.update(entry, collection_name)
                    inserted_entries += 1
                    if entry['number_of_aggregated'] != interval_size/300:
                        print "[%s/%s] entry[%s][number_of_aggregated] = %s" % \
                            (collection_name, coin, inserted_entries, entry['number_of_aggregated'])
                timestamp += interval_size
            print "[%s/%s] Updated %s entries" % (collection_name, coin, inserted_entries)

if __name__ == '__main__':
    main()
