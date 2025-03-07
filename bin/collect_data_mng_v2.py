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
import time
import calendar
from datetime import datetime
import requests

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname("__file__")))
sys.path.append("%s/lib/" % MYDIR)

from pymongo import MongoClient

client = MongoClient()

LOGFILE = "%s/log/fetch.log" % MYDIR
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    filename=LOGFILE,
    level=logging.INFO,
)

CURRENCIES = [
    "AUD",
    "BRL",
    "CAD",
    "CHF",
    "CLP",
    "CNY",
    "CZK",
    "DKK",
    "EUR",
    "GBP",
    "HKD",
    "HUF",
    "IDR",
    "ILS",
    "INR",
    "JPY",
    "KRW",
    "MXN",
    "MYR",
    "NOK",
    "NZD",
    "PHP",
    "PKR",
    "PLN",
    "RUB",
    "SEK",
    "SGD",
    "THB",
    "TRY",
    "TWD",
    "ZAR",
]

TIMESTAMP = [calendar.timegm(time.gmtime()) / 300 * 300]


def log(s):
    logging.error(s)


def fetch_coins(token):

    # url = "https://api.coinmarketcap.com/v1/ticker/"
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?start=1&limit=600&convert=USD"

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

    retry = 1
    while retry > 0:
        # try:
        headers = {"X-CMC_PRO_API_KEY": token, "Accept": "application/json"}
        response = requests.get(url, headers=headers)
        with open("/tmp/1.json", "w") as f:
            f.write(response.text)

        # t = requests.get(url)
        cmc_data = json.loads(response.text.encode("utf-8"))
        # cmc_data = json.loads(open("saved.data", "r").read())
        data = []
        for cmc_entry in cmc_data["data"]:
            entry = {}

            # adding legacy names to cmc_entry
            cmc_entry["rank"] = cmc_entry["cmc_rank"]
            cmc_entry["available_supply"] = cmc_entry["circulating_supply"] or 0
            cmc_entry["price_usd"] = cmc_entry["quote"]["USD"]["price"] or 0
            cmc_entry["24h_volume_usd"] = cmc_entry["quote"]["USD"]["volume_24h"] or 0
            cmc_entry["market_cap_usd"] = cmc_entry["quote"]["USD"]["market_cap"] or 0

            utc_dt = datetime.strptime(
                cmc_entry["last_updated"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            last_updated = (utc_dt - datetime(1970, 1, 1)).total_seconds()
            cmc_entry["last_updated"] = last_updated

            if TIMESTAMP[0]:
                timestamp = TIMESTAMP[0]
            else:

                timestamp = int(last_updated) / 300 * 300
                TIMESTAMP[0] = timestamp

            cmc_entry["timestamp"] = timestamp
            for field in fields:
                if field in int_fields:
                    entry[field] = int(cmc_entry[field])
                elif field in float_fields:
                    entry[field] = float(cmc_entry[field])
                else:
                    entry[field] = cmc_entry[field]

            data.append(entry)
        return data
    # except Exception as e:
    #     print e
    #     retry -= 1
    #     if retry:
    #         time.sleep(1)
    #     else:
    #         # log the error only in all retries not succeeded
    #         log("fetchng coins: %s, %s" % (e, field))
    #         return []


def fetch_marketcap(token):
    # url = "https://api.coinmarketcap.com/v1/global/"
    url = (
        "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest?convert=USD"
    )

    fields = [
        "total_market_cap_usd",
        "total_24h_volume_usd",
        "bitcoin_percentage_of_market_cap",
        "active_currencies",
        "active_assets",
        "active_markets",
        "last_updated",
        "timestamp",
    ]
    int_fields = [
        "active_currencies",
        "active_assets",
        "active_markets",
        "last_updated",
        "timestamp",
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

            headers = {"X-CMC_PRO_API_KEY": token, "Accept": "application/json"}
            response = requests.get(url, headers=headers)
            cmc_entry = json.loads(response.text)["data"]
            # cmc_entry = json.loads(open("marketcap.data", "r").read())["data"]

            cmc_entry["active_currencies"] = cmc_entry["active_cryptocurrencies"]
            # I do not know what is active_assets now, so I just use active_cryptocurrencies instead
            cmc_entry["active_assets"] = cmc_entry["active_cryptocurrencies"]
            cmc_entry["bitcoin_percentage_of_market_cap"] = cmc_entry["btc_dominance"]
            cmc_entry["total_market_cap_usd"] = cmc_entry["quote"]["USD"][
                "total_market_cap"
            ]
            cmc_entry["total_24h_volume_usd"] = cmc_entry["quote"]["USD"][
                "total_volume_24h"
            ]
            cmc_entry["active_markets"] = cmc_entry["active_exchanges"]

            utc_dt = datetime.strptime(
                cmc_entry["last_updated"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            last_updated = (utc_dt - datetime(1970, 1, 1)).total_seconds()
            cmc_entry["last_updated"] = last_updated

            if TIMESTAMP[0]:
                timestamp = TIMESTAMP[0]
            else:
                timestamp = int(cmc_entry["last_updated"]) / 300 * 300
                TIMESTAMP[0] = timestamp

            cmc_entry["timestamp"] = timestamp

            for field in fields:
                if field in int_fields:
                    entry[field] = int(cmc_entry[field])
                elif field in float_fields:
                    entry[field] = float(cmc_entry[field])
                else:
                    entry[field] = cmc_entry[field]

            break

        except Exception as e:
            print(e)
            retry -= 1
            if retry:
                time.sleep(1)
            else:
                # log the error only in all retries not succeeded
                log("fetching marketcap: %s" % e)

    return entry


def fetch_currencies(token):

    def fetch_one_currency(currency):

        retry = 1
        while retry > 0:
            try:
                url = (
                    "https://api.coinmarketcap.com/v1/ticker/bitcoin/?convert=%s"
                    % currency
                )

                t = requests.get(url)
                cmc_entry = json.loads(t.text)[0]

                if TIMESTAMP[0]:
                    timestamp = TIMESTAMP[0]
                else:
                    timestamp = int(cmc_entry["last_updated"]) / 300 * 300
                    TIMESTAMP[0] = timestamp

                price_usd = float(cmc_entry["price_usd"])
                price_currency = float(cmc_entry["price_%s" % currency.lower()])

                data = {
                    "last_updated": int(cmc_entry["last_updated"]),
                    "timestamp": timestamp,
                    currency: price_usd / price_currency,
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

    def get_currency_data():

        url = "http://data.fixer.io/api/latest?access_key=%s" % token

        response = requests.get(url)
        currency_data = json.loads(response.text)
        # currency_data = json.loads(open("currencies.data", "r").read())
        usd_rate = currency_data["rates"]["USD"]

        timestamp = int(currency_data["timestamp"]) / 300 * 300

        data = {
            "last_updated": currency_data["timestamp"],
            "timestamp": timestamp,
        }
        for currency, value in currency_data["rates"].items():
            data[currency] = usd_rate / value

        return data

    # data = {}
    # for currency in CURRENCIES:
    #     time.sleep(2)

    #     entry = fetch_one_currency(currency)
    #     data.update(entry)
    data = get_currency_data()

    return data


config_filename = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "etc/ratesx-config.json",
)
config = json.loads(open(config_filename, "r").read())

db = client.ratesx


if len(sys.argv) < 2:
    command = None
else:
    command = sys.argv[1]

if command == "marketcap":

    marketcap_data = fetch_marketcap(token=config["cmc"])
    if marketcap_data:
        marketcap = db.marketcap
        # print json.dumps(marketcap_data, indent=4)
        marketcap.insert_one(marketcap_data)

elif command == "currencies":

    currencies = db.currencies
    currencies_data = fetch_currencies(token=config["fixer"])
    # print json.dumps(currencies_data, indent=4)
    currencies.insert_one(currencies_data)

elif command == "coins":

    coins = db.coins
    coins_data = fetch_coins(token=config["cmc"])

    if coins_data:
        # pass
        # print json.dumps(data, indent=4)
        coins.insert_many(coins_data)
