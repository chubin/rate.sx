"""

This programs fetch data from coinmarketcap and saves it in a local mongodb database.

Collections:

   coins
   currencies
   marktcap

<coins>:

	{
        "symbol":           "BTC",
        "timestamp":        "1472761800"
        "rank":             "1",
        "price_usd":        "573.137",
        "24h_volume_usd":   "72855700.0",
        "market_cap_usd":   "9080883500.0",
        "available_supply": "15844176.0",
        "total_supply":     "15844176.0",
        "last_updated":     "1472762067"
    }

symbol and timesatmp are indices.


<marketcap>:

    {
        "total_market_cap_usd": 201241796675,
        "total_24h_volume_usd": 4548680009,
        "bitcoin_percentage_of_market_cap": 62.54,
        "active_currencies": 896,
        "active_assets": 360,
        "active_markets": 6439,
        "last_updated": 1509909852
        "timestamp": 1509909600,
    }

<currencies>:

    {
        "symbol":       "EUR",
        "timestamp":    "1472761800",
        "price_usd":    "1.15",
    }
"""

import sys
import os
import json
import logging
import requests
import time
import calendar

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname('__file__')))
sys.path.append("%s/lib/" % MYDIR)

from pymongo import MongoClient
client = MongoClient()

LOGFILE="%s/log/fetch.log" % MYDIR
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    filename=LOGFILE,
    level=logging.INFO)

CURRENCIES = [ 
    "AUD", "BRL", "CAD", "CHF", "CLP", "CNY", "CZK", "DKK", "EUR", "GBP", 
    "HKD", "HUF", "IDR", "ILS", "INR", "JPY", "KRW", "MXN", "MYR", "NOK",
    "NZD", "PHP", "PKR", "PLN", "RUB", "SEK", "SGD", "THB", "TRY", "TWD",
    "ZAR"
]

TIMESTAMP = [calendar.timegm(time.gmtime())/300*300]

def log(s):
    logging.error(s)

def fetch_coins(start=0):
    
    url = "https://api.coinmarketcap.com/v1/ticker/"
    if start != 0:
        url += "?start=%s" % start

    fields = [
        "symbol",
        "timestamp",
        "rank",
        "price_usd",
        "24h_volume_usd",
        "market_cap_usd",
        "available_supply",
        "total_supply",
        "last_updated",
    ]
    int_fields = [
        "rank",
        "last_updated",
    ]
    float_fields = [
        "available_supply",
        "total_supply",
        "price_usd",
        "24h_volume_usd",
        "market_cap_usd",
    ]

    retry = 3
    while retry > 0:
        try:
            t = requests.get(url)
            cmc_data = json.loads(t.text)
            data = []
            for cmc_entry in cmc_data:
                entry = {}

                if TIMESTAMP[0]:
                    timestamp = TIMESTAMP[0]
                else:
                    timestamp = int(cmc_entry['last_updated'])/300*300
                    TIMESTAMP[0] = timestamp

                cmc_entry['timestamp'] = timestamp
                for field in fields:
                    if field in int_fields:
                        entry[field] = int(cmc_entry[field])
                    elif field in float_fields:
                        entry[field] = float(cmc_entry[field])
                    else:
                        entry[field] = cmc_entry[field]
                data.append(entry)
            return data
        except Exception as e:
            retry -= 1
            if retry:
                time.sleep(1)
            else:
                # log the error only in all retries not succeeded
                log("fetchng coins, %s: %s, %s" % (start, e, field))
                return []

def fetch_marketcap():
    url = "https://api.coinmarketcap.com/v1/global/"

    fields = [
        "total_market_cap_usd",
        "total_24h_volume_usd",
        "bitcoin_percentage_of_market_cap",
        "active_currencies",
        "active_assets",
        "active_markets",
        "last_updated",
        "timestamp"
    ]
    int_fields = [
        "active_currencies",
        "active_assets",
        "active_markets",
        "last_updated",
        "timestamp"
    ]
    float_fields = [
        "total_market_cap_usd",
        "total_24h_volume_usd",
        "bitcoin_percentage_of_market_cap",
    ]

    entry = {}

    retry = 3
    while retry > 0:
        try:

            t = requests.get(url)
            cmc_entry = json.loads(t.text)

            if TIMESTAMP[0]:
                timestamp = TIMESTAMP[0]
            else:
                timestamp = int(cmc_entry['last_updated'])/300*300
                TIMESTAMP[0] = timestamp

            cmc_entry['timestamp'] = timestamp

            for field in fields:
                if field in int_fields:
                    entry[field] = int(cmc_entry[field])
                elif field in float_fields:
                    entry[field] = float(cmc_entry[field])
                else:
                    entry[field] = cmc_entry[field]

            break

        except Exception as e:
            retry -= 1
            if retry:
                time.sleep(1)
            else:
                # log the error only in all retries not succeeded
                log("fetching marketcap: %s" %e)

    return entry

def fetch_currencies():

    def fetch_one_currency(currency):
        
        retry = 3
        while retry > 0:
            try:
                url = "https://api.coinmarketcap.com/v1/ticker/bitcoin/?convert=%s" % currency

                t = requests.get(url)
                cmc_entry = json.loads(t.text)[0]

                if TIMESTAMP[0]:
                    timestamp = TIMESTAMP[0]
                else:
                    timestamp = int(cmc_entry['last_updated'])/300*300
                    TIMESTAMP[0] = timestamp

                price_usd = float(cmc_entry['price_usd'])
                price_currency = float(cmc_entry['price_%s' % currency.lower()])

                data = {
                    'last_updated': int(cmc_entry['last_updated']),
                    'timestamp': timestamp,
                    currency: price_usd/price_currency,
                }
                break
            except Exception as e:
                retry -= 1
                if retry:
                    time.sleep(1)
                else:
                    # log the error only in all retries not succeeded
                    log("fetching currency: %s: %s" % (currency, e))
        
        return data

    data = {}
    for currency in CURRENCIES:
        time.sleep(2)

        entry = fetch_one_currency(currency)
        data.update(entry)

    return data

db = client.ratesx
coins = db.coins
marketcap = db.marketcap
currencies = db.currencies

currencies_data = fetch_currencies()

coins_data = []
for i in range(5):
    data = fetch_coins(start=100*i)
    coins_data.append(data)
    time.sleep(5)

marketcap_data = fetch_marketcap()

# insert data into mongodb

currencies.insert(currencies_data)

if marketcap_data != []:
    marketcap.insert(marketcap_data)

for data in coins_data:
    if data != []:
        coins.insert_many(data)


