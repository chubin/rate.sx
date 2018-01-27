"""
MongoDB client.
Exports MonfoReader
"""

import sys
import os
import datetime

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname('__file__')))
sys.path.append("%s/lib/" % MYDIR)

import currencies_names
from pymongo import MongoClient

#
# functions that fetch needed data from mongodb
#

class MongoReader(object):
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
            price_before = self.coins\
                .find({"symbol": symbol, "timestamp":{'$lt':timestamp-timedelta+1}}) \
                .sort([("timestamp", -1)]) \
                .limit(1)[0]['price_usd']

            price_before = price_before*self.currency_factor(timestamp=timestamp-timedelta)
            price = price_usd*self.currency_factor(timestamp=timestamp)

            return (price-price_before)*100/price_before

        if timestamp is None:
            timestamp = self.coins \
                        .find({}, {"timestamp":1}) \
                        .sort([("timestamp", -1)]) \
                        .limit(1)[0]['timestamp']

        number_of_coins = self.number_of_coins

        data = []
        for entry in self.coins.find({"rank": {"$lt": number_of_coins + 1}, "timestamp":timestamp}):
            entry = {
                'code': entry['symbol'],
                'price': entry['price_usd']*self.currency_factor(timestamp=timestamp),
                'change_24h': get_change(entry['symbol'], entry['price_usd'], timestamp, 24*3600),
                'change_1h': get_change(entry['symbol'], entry['price_usd'], timestamp, 3600),
                'cap': entry['market_cap_usd']*self.currency_factor(timestamp),
                'spark': self.load_spark(entry['symbol'], timestamp),
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


