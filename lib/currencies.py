#!/usr/bin/python
# vim: encoding=utf-8

import os
import requests
import json
import calendar
import time

"""
This file can be imported for currency related functions.
It is also used as a program to gather currency data.

Currencies data is gathered every five minutes using cron (see crontab).
Data is stored in CURRENCIES_FILE.

At the moment data is stored in a plain file.
It will be moved to a mongodb server later.

Exported functions:

    get_currency_rate_btc
    get_currency_rate_usd
    get_currency_rate_to_usd
    get_currency_rate

At the moment functions are returning only current values
"""

CURRENCIES_FILE = "/home/igor/rate.sx/data/currencies/now"
CRYPTOS_DIR = "/home/igor/rate.sx/data"

SUPPORTED_CURRENCIES = [
    "AUD", "BRL", "CAD", "CHF", "CLP", "CNY", "CZK", "DKK", "EUR", "GBP",
    "HKD", "HUF", "IDR", "ILS", "INR", "JPY", "KRW", "MXN", "MYR", "NOK",
    "NZD", "PHP", "PKR", "PLN", "RUB", "SEK", "SGD", "THB", "TRY", "TWD",
    "ZAR"
]

SUPPORTED_CURRENCIES = ['USD', 'AUD', "CAD", 'CHF', 'CNY', 'EUR', 'GBP', 'IDR', 'JPY', 'KRW', 'RUB']

SYMBOL = {
    'USD': '$',
    'AUD': '$',
    'CAD': '$',
    'CHF': 'CHF ',
    'CNY': '¥',
    'EUR': '€',
    'GBP': '£',
    'IDR': '₹',
    'JPY': '¥',
    'KRW': '₩',
    'RUB': '₽'
}

CRYPTO_CURRENCIES = ['BTC', 'ETH', 'BCH', 'XRP', 'MIOTA', 'DASH', 'LTC', 'BTG', 'XMR']

def _log(message):
    timestamp = calendar.timegm(time.gmtime())
    print "%s %s" % (timestamp, message)
    pass

def _get_last_lines(filename, number=1):
    with open(filename, 'rb') as fh:
        try: 
            fh.seek(-1024*4, os.SEEK_END)
        except:
            pass

        try:
            last = [x.decode() for x in fh.readlines()[-number:]]
        except IndexError:
            return []
        return last

def _fetch_currencies():
    """
    Fetch current currencies rates.
    Returns vector.
    """
    prices_vector = []
    for currency in SUPPORTED_CURRENCIES[1:]:
        url = 'https://api.coinmarketcap.com/v1/ticker/bitcoin/?convert=%s' % currency
        data = json.loads(requests.get(url).text)[0]
        price_currency = data['price_%s' % currency.lower()]
        prices_vector.append(price_currency)
    prices_vector = [data['price_usd']] + prices_vector
    return prices_vector

def _save_currencies(prices_vector):
    timestamp = calendar.timegm(time.gmtime())
    with open(CURRENCIES_FILE, 'a') as f:
        f.write("%s %s\n" % (str(timestamp), " ".join(prices_vector)))

def get_currency_rate_btc(currency):
    """
    Returns current price for 1 BTC in specified currency
        or -1 if something is wrong (unknown currency, corrupeted file, etc.)
    """

    if currency not in SUPPORTED_CURRENCIES:
        _log("Unknown currency: %s" % currency)
        return None
    last_line = _get_last_lines(CURRENCIES_FILE)
    if len(last_line) == 0:
        return None
    last_line = last_line[-1]

    try:
        values = [float(x) for x in last_line.split()[1:]]
    except:
        # something is wrong
        # some of the currencies could not be converted to a float
        _log("Some of the currencies can't be converted to float")
        return None

    if len(values) != len(SUPPORTED_CURRENCIES):
        _log("Wrong number of currencies")
        return None

    currency_value = dict(zip(SUPPORTED_CURRENCIES, values))
    return currency_value.get(currency, -1)

def get_currency_rate_usd(currency):
    """
    Returns current rate of usd/currency
    """
    btc_usd = get_currency_rate_btc('USD')
    btc_currency = get_currency_rate_btc(currency)

    if btc_usd is None or btc_currency is None:
        return None

    return btc_currency/btc_usd

def get_currency_rate_to_usd(currency):
    """
    Returns current rate of currency/usd 
    """
    btc_usd = get_currency_rate_btc('USD')
    btc_currency = get_currency_rate_btc(currency)

    if btc_usd is None or btc_currency is None:
        return None

    return btc_usd/btc_currency

def get_currency_rate(currency_from, currency_to):
    """
    Returns current rate of currency_from/currency_to
    """
    btc_currency_from = get_currency_rate_btc(currency_from)
    btc_currency_to = get_currency_rate_btc(currency_to)

    if btc_currency_from is None or btc_currency_to is None:
        return None

    return btc_currency_to/btc_currency_from

def get_crypto_rate_to_usd(crypto):
    """
    Returns current rate of crypto/usd 
    """
    if crypto not in CRYPTO_CURRENCIES:
        return None
    filename = os.path.join(CRYPTOS_DIR, crypto)
    if not os.path.exists(filename):
        _log("Cannot find cryptocurrency file")
        return None

    last_line = _get_last_lines(filename)
    if len(last_line) == 0:
        return None
    last_line = last_line[-1]

    try:
        value = float(last_line.split()[1])
    except:
        # something is wrong
        # some of the currencies could not be converted to a float
        _log("Currency can't be converted to float")
        return None

    return value

def get_rate_to_usd(currency):
    if currency in CRYPTO_CURRENCIES:
        return get_crypto_rate_to_usd(currency)
    else:
        return get_currency_rate_to_usd(currency)

def _main():
    prices_vector = _fetch_currencies()
    _save_currencies(prices_vector)

if __name__ == "__main__":
    _main()

