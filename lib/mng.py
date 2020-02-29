"""
MongoDB client.
Exports MonfoReader
"""

import sys
import os
import datetime
from pymongo import MongoClient, ASCENDING

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname('__file__')))
sys.path.append("%s/lib/" % MYDIR)

# pylint: disable=wrong-import-position
import currencies_names
# pylint: enable=wrong-import-position

#
# functions that fetch needed data from mongodb
#

class MongoReader(object):  # pylint: disable=too-many-instance-attributes
    """
    MongDB client
    """
    def __init__(self, config=None):

        self.client = MongoClient()

        ratesx_db = self.client.ratesx
        self.coins = ratesx_db.coins
        self.marketcap = ratesx_db.marketcap
        self.currencies = ratesx_db.currencies

        if config is None:
            config = {}
        self.number_of_coins = config.get('number_of_coins', 30)
        self.number_of_ticks = config.get('number_of_ticks', 12)
        self.currency = config.get('currency', 'USD')

        if self.currency in currencies_names.SUPPORTED_CURRENCIES:
            self.is_currency_coin = False
        else:
            self.is_currency_coin = True

        self._currency_factor_cache = {}
        self._spark_price_currency_ticks = []

    def currency_factor(self, timestamp=None, currency=None):
        """
        Factor that is used to convert value in <self.currency> in USD
        for specified <timestamp>
        """

        if currency is None:
            currency = self.currency

        if currency in currencies_names.SUPPORTED_CURRENCIES:
            is_currency_coin = False
        else:
            is_currency_coin = True

        if currency == 'USD':
            return 1

        # we use cache only if timestamp is specified
        if timestamp and (currency, timestamp) in self._currency_factor_cache:
            return self._currency_factor_cache[(currency, timestamp)]

        query = {}
        if timestamp:
            query["timestamp"] = {'$lt':timestamp+1}

        if is_currency_coin:
            query.update({"symbol": currency})
            try:
                price_symbol = self.coins\
                    .find(query, {'price_usd':1}) \
                    .sort([("timestamp", -1)]) \
                    .limit(1)[0]['price_usd']
            except IndexError:
                raise ValueError("Unknown coin/currency: %s" % currency)
        else:
            query.update({currency: {'$exists': True}})
            try:
                price_symbol = self.currencies.find(query, {currency:1}) \
                    .sort([("timestamp", -1)]) \
                    .limit(1)[0][currency]
            except IndexError:
                raise ValueError("Unknown currency: %s" % currency)

        # we use cache only if timestamp is specified
        if timestamp:
            self._currency_factor_cache[(currency, timestamp)] = 1/price_symbol

        return 1/price_symbol

    def load_spark(self, symbol, timestamp):
        """
        Generate spakrline for the <code> coin or for marktcap
        """

        ticks = self.number_of_ticks + 1
        price_usd_ticks = [
            (x['timestamp'], x['price_usd']) for x in self.coins\
                .find({"symbol": symbol, "timestamp":{'$lt':timestamp+1}}) \
                .sort([("timestamp", -1)]) \
                .limit(ticks)][::-1]
        price_usd_ticks = [x[1] for x in price_usd_ticks]

        if self.currency == 'USD':
            price_ticks = price_usd_ticks
        elif self.is_currency_coin:
            if self._spark_price_currency_ticks == []:
                self._spark_price_currency_ticks = [
                    x['price_usd'] for x in self.coins\
                        .find({"symbol": self.currency, "timestamp":{'$lt':timestamp+1}}) \
                        .sort([("timestamp", -1)]) \
                        .limit(ticks)][::-1]
            price_ticks = [x/y for x, y in zip(price_usd_ticks, self._spark_price_currency_ticks)]
        else:
            if self._spark_price_currency_ticks == []:
                self._spark_price_currency_ticks = [
                    x[self.currency] for x in self.currencies\
                        .find({self.currency: {'$exists': True}, "timestamp":{'$lt':timestamp+1}}) \
                        .sort([("timestamp", -1)]) \
                        .limit(ticks)][::-1]
            price_ticks = [x/y for x, y in zip(price_usd_ticks, self._spark_price_currency_ticks)]

        return price_ticks


    def mng_load_marketcap_global_data(self, timestamp=None):
        """
        Load marketcap data from MongoDB
        """

        if timestamp is None:
            data = self.marketcap.find().sort([('timestamp', -1)]).limit(1)[0]
            timestamp = data['timestamp']
        else:
            timestamp = self.coins \
                        .find({}, {"timestamp":1}) \
                        .sort([("timestamp", -1)]) \
                        .limit(1)[0]['timestamp']
            data = self.marketcap.find_one({'timestamp':timestamp})

        answer = {}
        for field in ["active_currencies",
                      "bitcoin_percentage_of_market_cap",
                      "last_updated",
                      "total_market_cap_usd",
                      "active_markets",
                      "active_assets",
                      "total_24h_volume_usd"]:
            if field.endswith('_usd'):
                answer[field] = self.currency_factor(timestamp=timestamp)*data[field]
            else:
                answer[field] = data[field]

        return answer

    def mng_load_coins_data(self, timestamp=None):
        """
        Load coins data from MongoDB
        """

        def get_change(symbol, price_usd, timestamp, timedelta):
            """
            Find change (in percents) of <symbols> between <timestamp>-<timedelta> and <timestamp>
            """
            try:
                price_before = self.coins\
                    .find({"symbol": symbol, "timestamp":{'$lt':timestamp-timedelta+1}}) \
                    .sort([("timestamp", -1)]) \
                    .limit(1)[0]['price_usd']
            except IndexError:
                price_before = 0

            price_before = price_before*self.currency_factor(timestamp=timestamp-timedelta)
            price = price_usd*self.currency_factor(timestamp=timestamp)

            if price_before != 0:
                return (price-price_before)*100/price_before
            else:
                return 0

        if timestamp is None:
            timestamp = self.coins \
                        .find({}, {"timestamp":1}) \
                        .sort([("timestamp", -1)]) \
                        .limit(1)[0]['timestamp']

        number_of_coins = self.number_of_coins

        data = []
        for entry in self.coins.find({"rank": {"$lt": number_of_coins + 1}, "timestamp":timestamp}):
            try:
                symbol = entry['symbol']
            except KeyError:
                symbol = '-'

            try:
                price = entry['price_usd']*self.currency_factor(timestamp=timestamp)
            except KeyError:
                price = '-'

            try:
                change_24h = get_change(entry['symbol'], entry['price_usd'], timestamp, 24*3600)
            except KeyError:
                change_24h = '-'

            try:
                change_1h = get_change(entry['symbol'], entry['price_usd'], timestamp, 3600)
            except KeyError:
                change_1h = '-'

            try:
                cap = entry['market_cap_usd']*self.currency_factor(timestamp)
            except KeyError:
                cap = '-'

            try:
                spark = self.load_spark(entry['symbol'], timestamp)
            except KeyError:
                spark = '-'

            entry = {
                'code': symbol,
                'price': price,
                'change_24h': change_24h,
                'change_1h': change_1h,
                'cap': cap,
                'spark': spark,
            }
            data.append(entry)

        return data


    def load_from_mongo(self):
        """
        load all data from mongodb
        """

        return {
            'data': self.mng_load_coins_data(),
            'marketcap_global_data': self.mng_load_marketcap_global_data(),
            'timestamp_now': "%s UTC" % datetime.datetime.utcnow(),
        }

    def get_raw_data(self, coin, start_time, stop_time, fields=None, collection_name=None): #pylint: disable=too-many-arguments
        """
        Load raw ``coin`` data from _start_time_ (>=) to _stop_time_ (<).
        If ``coin`` is None (for currencies), get all data.
        """

        if collection_name:
            coins = self.client.ratesx[collection_name]
        else:
            coins = self.coins

        if coin:
            query = {'symbol':   coin,}
        else:
            query = {}

        query.update({
            'timestamp': {'$gt': start_time - 1, '$lt': stop_time},
        })

        sort_key = [("timestamp", 1)]
        if fields:
            data = [x for x in coins.find(query, fields).sort(sort_key)]
        else:
            data = [x for x in coins.find(query).sort(sort_key)]
        return data

    def get_first_timestamp(self, coin, last=False, collection_name=None):
        """
        First timestamp for ``coin`` in database.
        If ``coin`` is None, check all entries (used for currencies).
        """

        if collection_name:
            coins = self.client.ratesx[collection_name]
        else:
            coins = self.coins

        if coin:
            query = {'symbol':   coin,}
        else:
            query = {}

        if last:
            sort_key = [("timestamp", -1)]
        else:
            sort_key = [("timestamp", 1)]
        data = [x for x in coins.find(query, {'timestamp': 1}).sort(sort_key).limit(1)]
        if data != []:
            return data[0]['timestamp']
        return None

class MongoWriter(object):
    """
    MongoDB writer client.
    Provides insert() for data writing.
    """

    def __init__(self):

        self.client = MongoClient()

        ratesx_db = self.client.ratesx
        self.coins = ratesx_db.coins
        self.marketcap = ratesx_db.marketcap
        self.currencies = ratesx_db.currencies

        self.allowed_collections = ['coins_1h', 'coins_24h', 'currencies_1h']

    def _get_collection(self, collection_name=None):
        if collection_name:
            if collection_name in self.allowed_collections:
                coins = self.client.ratesx[collection_name]
            else:
                raise KeyError("Not allowed collection name: %s" % collection_name)
        else:
            coins = self.coins

        if collection_name \
            and collection_name not in self.client.ratesx.collection_names():

            if collection_name.startswith('coins_'):
                coins.create_index([('symbol', ASCENDING)], unique=False)
                coins.create_index([('timestamp', ASCENDING)], unique=False)
                coins.create_index([('symbol', ASCENDING),
                                    ('timestamp', ASCENDING)], unique=True)

            if collection_name.startswith('currencies_'):
                coins.create_index([('timestamp', ASCENDING)], unique=False)

        return coins

    def update(self, entry, collection_name=None):
        "coll.replace_one() wrapper"

        coins = self._get_collection(collection_name)
        if 'symbol' in entry:
            coins.replace_one(
                {'symbol':entry['symbol'], 'timestamp':entry['timestamp']}, entry, True)
        else:
            coins.replace_one(
                {'timestamp':entry['timestamp']}, entry, True)

    def insert_many(self, entries, collection_name=None):
        "coll.insertMany() wrapper"

        coins = self._get_collection(collection_name)
        coins.insertMany(entries)
