#!/usr/bin/python
# vim: encoding=utf-8

import sys
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

SUPPORTED_CURRENCIES = [
    "AUD", "BRL", "CAD", "CHF", "CLP", "CNY", "CZK", "DKK", "EUR", "GBP",
    "HKD", "HUF", "IDR", "ILS", "INR", "JPY", "KRW", "MXN", "MYR", "NOK",
    "NZD", "PHP", "PKR", "PLN", "RUB", "SEK", "SGD", "THB", "TRY", "TWD",
    "ZAR"
]

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

