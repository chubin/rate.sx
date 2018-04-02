
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

from currencies_names import currency_name
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

def aggregate_currencies(_, time_start, interval):
    """
    ``coin`` is always None; it is used here, because I want to merge aggregation
    function later.

    Aggregate 5min currencies data starting from _start_time_
    for _interval_ (in seconds; must be divisible by 5m)
    and return aggregated information (dictionary).

    Fields of the result: min, max, avg, begin, end
    """

    time_end = time_start + interval
    entries = MONGO_READER.get_raw_data(None, time_start, time_end, collection_name='currencies')

    result = {
        'timestamp': entries[0].get('timestamp'),
        'time_end': entries[-1].get('timestamp'),
        'number_of_aggregated': len(entries),
    }
    currencies = [k for k in entries[0].keys()
                  if not k.startswith('_') and k not in ['timestamp', 'last_updated']]
    for key in currencies:
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

    desired_interval = (time_end-time_start)/number_of_ticks

    chosen_interval = None
    for interval_name, interval_size in sorted(INTERVAL.items(), key=lambda x: -x[1]):
        if interval_size < desired_interval:
            chosen_interval = interval_name

    # if interval is so small, we need to use the raw and not the aggregated data
    collection_name = None
    if chosen_interval:
        collection_name = 'coins_%s' % chosen_interval

    entries = MONGO_READER.get_raw_data(coin, time_start, time_end, collection_name=collection_name)
    if entries == []:
        return {'meta':{}, 'ticks':[]}

    if key is None:
        key = "price_usd"

    meta = {}
    ticks = []
    sum_ = 0

    if collection_name is None:
        # not aggregated data
        meta = {
            'symbol': entries[0]['symbol'],
            'begin': entries[0][key],
            'end': entries[-1][key],
            'time_begin': entries[0]['timestamp'],
            'time_end': entries[-1]['timestamp'],

            'min': entries[0][key],
            'max': entries[0][key],
            'time_min': entries[0]['timestamp'],
            'time_max': entries[0]['timestamp'],
            }

        for entry in entries:
            ticks.append(entry[key])
            sum_ += entry[key]

            if entry[key] > meta['max']:
                meta['max'] = entry[key]
                meta['time_max'] = entry['timestamp']

            if entry[key] < meta['min']:
                meta['min'] = entry[key]
                meta['time_min'] = entry['timestamp']
    else:
        # aggregated data

        # this parameter should be taken to the ticks
        take_this = 'avg'

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

def get_aggregated_pair(coin1, coin2, time_start, time_end, number_of_ticks, key=None): # pylint: disable=too-many-locals,too-many-arguments,too-many-branches,too-many-statements
    """
    Aggregate coin pairs (or coin and currency pairs).
    It works this way: find data for ``coin1`` and find data for ``coin2``,
    after that divide ``coin1`` data by ``coin2`` pairwise.
    This method is approximate for aggregated values.
    ``coin2`` can be a currency.
    """

    coin2_is_currency = bool(currency_name(coin2))

    desired_interval = (time_end-time_start)/number_of_ticks

    chosen_interval = None
    for interval_name, interval_size in sorted(INTERVAL.items(), key=lambda x: -x[1]):
        if interval_size < desired_interval:
            chosen_interval = interval_name

    # if interval is so small, we need to use the raw and not the aggregated data
    collection_name = None
    if chosen_interval:
        collection_name = 'coins_%s' % chosen_interval

    if key is None:
        key = "price_usd"

    entries1 = MONGO_READER.get_raw_data(
        coin1, time_start, time_end, collection_name=collection_name)
    if entries1 == []:
        return {'meta':{}, 'ticks':[]}

    # depeding on (1) that we have a currency in coin2 or not
    # and (2) if data is aggregated, we have to read entries2 from different collections
    # and in one case postprocess them
    if collection_name is None and coin2_is_currency:

        if collection_name is None:
            currencies_collection = 'currencies'
        else:
            currencies_collection = collection_name.replace('coins_', 'currencies_')

        fields = {'timestamp': 1, coin2: 1}
        entries2 = MONGO_READER.get_raw_data(
            None, time_start, time_end,
            collection_name=currencies_collection,
            fields=fields)

        new_entries2 = []
        for entry in entries2:
            entry.update({key: entry[coin2]})
            new_entries2.append(entry)
        entries2 = new_entries2

    else:
        entries2 = MONGO_READER.get_raw_data(
            coin2, time_start, time_end, collection_name=collection_name)

    # print "len(entries2) = ", len(entries2)

    meta = {}
    ticks = []
    sum_ = 0

    if collection_name is None:
        # not aggregated data
        meta = {
            'symbol': entries1[0]['symbol'],
            'begin': entries1[0][key]/entries2[0][key],
            'end': entries1[-1][key]/entries2[-1][key],
            'time_begin': entries1[0]['timestamp'],
            'time_end': entries1[-1]['timestamp'],

            'min': entries1[0][key]/entries2[0][key],
            'max': entries1[0][key]/entries2[0][key],
            'time_min': entries1[0]['timestamp'],
            'time_max': entries1[0]['timestamp'],
            }

        for entry1, entry2 in zip(entries1, entries2):
            this_value = entry1[key]/entry2[key]
            ticks.append(this_value)
            sum_ += this_value

            if this_value > meta['max']:
                meta['max'] = this_value
                meta['time_max'] = entry1['timestamp']

            if this_value < meta['min']:
                meta['min'] = this_value
                meta['time_min'] = entry1['timestamp']
    else:
        # aggregated data

        # this parameter should be taken to the ticks
        take_this = 'avg'

        meta = {
            'symbol': entries1[0]['symbol'],
            'begin': entries1[0][key]['begin']/entries2[0][key]['begin'],
            'end': entries1[-1][key]['end']/entries2[-1][key]['end'],
            'time_begin': entries1[0]['timestamp'],
            'time_end': entries1[-1]['time_end'],

            'min': entries1[0][key]['min']/entries2[0][key]['max'],
            'max': entries1[0][key]['max']/entries2[0][key]['min'],
            'time_min': entries1[0][key]['time_min'],
            'time_max': entries1[0][key]['time_max'],
            }

        for entry1, entry2 in zip(entries1, entries2):
            this_value = entry1[key][take_this]/entry2[key][take_this]
            ticks.append(this_value)
            sum_ += this_value

            if this_value > meta['max']:
                meta['max'] = this_value
                meta['time_max'] = entry1[key]['time_max']

            if this_value < meta['min']:
                meta['min'] = this_value
                meta['time_min'] = entry1[key]['time_min']

    meta['avg'] = sum_/len(ticks)

    return {
        'ticks': ticks,
        'meta': meta,
    }

def aggregate_new_entries(coin):
    """
    Aggregate new entries for ``coin``. If ``coin`` is none, aggregate currencies.
    """

    if coin:
        aggregation_function = aggregate_coin
        collection_prefix = 'coins_'
    else:
        aggregation_function = aggregate_currencies
        collection_prefix = 'currencies_'

    first_timestamp = MONGO_READER.get_first_timestamp(coin)
    last_timestamp = MONGO_READER.get_first_timestamp(coin, last=True)

    for interval_name, interval_size in INTERVAL.items():
        collection_name = collection_prefix + interval_name

        last_aggregated_timestamp = \
            MONGO_READER.get_first_timestamp(coin, last=True, collection_name=collection_name)
        if last_aggregated_timestamp is None:
            print "[%s/%s] last_aggregated_timestamp is None" % (collection_name, coin)
            last_aggregated_timestamp = first_timestamp
        print "[%s/%s] %s entries to insert/update" % \
            (collection_name, coin,
             int(math.ceil((last_timestamp - last_aggregated_timestamp)*1.0/interval_size)))

        inserted_entries = 0
        timestamp = last_aggregated_timestamp
        while timestamp <= last_timestamp:
            entry = aggregation_function(coin, timestamp, interval_size)

            #import json
            #print json.dumps(entry)

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

def do_coins():
    """
    Aggregator of existing entries
    """

    AGGREGATE_COINS = [
        'BTC', 'ETH', 'XRP', 'BCH', 'LTC', 'EOS',
        'ADA', 'XLM', 'NEO', 'MIOTA', 'XMR',
    ]
    for coin in AGGREGATE_COINS: # ['BTC', 'ETH', 'XRP']:
        aggregate_new_entries(coin)

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

def main():
    """
    Aggregator of existing entries
    """
    coins_to_aggregate = [
        None,
        'BTC', 'ETH', 'XRP', 'BCH', 'LTC', 'EOS',
        'ADA', 'XLM', 'NEO', 'MIOTA', 'XMR',
    ]
    for coin in coins_to_aggregate:
        aggregate_new_entries(coin)

if __name__ == '__main__':
    main()
