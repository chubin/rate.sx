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
Data is stored in MongoDB.

Exported functions:

    get_rate_to_usd

"""

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname("__file__")))
sys.path.append(f"{MYDIR}/lib/")

from mng import MongoReader

mongo_reader = MongoReader()


def get_rate_to_usd(currency, timestamp=None):
    return 1 / mongo_reader.currency_factor(timestamp=timestamp, currency=currency)


def _main():
    pass


if __name__ == "__main__":
    _main()
