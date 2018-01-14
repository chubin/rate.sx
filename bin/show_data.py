#!/usr/bin/python
# vim: encoding=utf-8

"""
command line terminal rate.sx client
"""

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import os

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname('__file__')))
sys.path.append("%s/lib/" % MYDIR)

from mng import MongoReader
from view_ansi import print_table

def main():
    "main function"

    config = {
        'number_of_ticks': 12,
        'number_of_coins': 10,
        'currency': 'USD',
    }
    if len(sys.argv) > 1:
        config['currency'] = sys.argv[1]
    mongo_reader = MongoReader(config)
    data = mongo_reader.load_from_mongo()

    market_cap_direction, vol_24h_direction, btc_dominance_direction = 0, 0, 0
    marktcap_spark = "."*48

    sys.stdout.write(
        print_table(
            config['currency'],
            data,
            (market_cap_direction, vol_24h_direction, btc_dominance_direction),
            marktcap_spark))

main()

