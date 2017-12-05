#!/usr/bin/python
# vim: encoding=utf-8

"""
Todo:

* save parased data
* eur/usd switch
* darkgray frame
* sparks
* web version
"""

import sys
import os
import requests
import json
import yaml
import locale
import calendar
import time
import subprocess
import datetime

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

from terminaltables import SingleTable
from colorama import Fore, Back, Style 
from termcolor import colored

MYDIR = os.path.abspath(os.path.dirname( os.path.dirname('__file__') ))
sys.path.append("%s/lib/" % MYDIR)
from to_precision import to_precision
import spark
import currencies

DRY_RUN = False
FETCH = True

HEADER = r"""
                                                            X          _               Y
                                                            X _ _ __ _| |_ ___  ____ __Y
                                                            X| '_/ _` |  _/ -_)(_-< \ /Y     
__ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZX__________|_| \__,_|\__\___()__/_\_\_____Y
 '           '           '           '           '                                           """

HEADER = HEADER.replace('X', '\033[33m').replace('Y', '\033[32m')

#FOLLOW_ME = '[Follow \033[46m\033[30m@igor_chubin\033[0m for rate.sx updates]' + Style.RESET_ALL
FOLLOW_ME = '[Follow \033[46m\033[30m@igor_chubin\033[0m for updates]' + Style.RESET_ALL
FOLLOW_ME = Fore.CYAN + '[Follow @igor_chubin for rate.sx updates]' + Style.RESET_ALL
NEW_FEATURE = 'See ' + Fore.GREEN + 'rate.sx/:help' + Style.RESET_ALL + ' for help and disclaimer'
GITHUB_BUTTON = ' ' + '\033[100;30m' + '[github.com/chubin/rate.sx]' + Style.RESET_ALL

#
# data handling functions
#

def get_data_text():
    cmd = ["/home/igor/rate.sx/bin/cmd-data"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return stdout

def save_data(entry):
    code = entry['code']
    filename = 'data/%s' % code
    timestamp = calendar.timegm(time.gmtime())
    if not DRY_RUN:
        with open(filename, 'a') as f:
            f.write("%s %s %s %s %s\n" % (timestamp, entry['price'], entry['change_24h'], entry['change_1h'], entry['cap']))

def get_last_line(filename, number=1):
    with open(filename, 'rb') as fh:
        try: 
            fh.seek(-1024*4, os.SEEK_END)
        except:
            pass

        try:
            last = [x.decode() for x in fh.readlines()[-number:]]
        except IndexError:
            # returns zeroes if the file is empty
            return ['0 0 0 0 0']
        return last

def parse_data(text):

    lines = text.splitlines()[3:]

    data = []
    rank = 0
    for line in lines:
        if '----' in line:
            continue
        parts = line.strip().split()
        code = parts[3]
        price = float(parts[5])
        change_24h = float(parts[7][:-1])
        change_1h = float(parts[9][:-1])
        cap = parts[11]
        if cap[-1] == 'B':
            cap = float(cap[:-1])*1000000000
        elif cap[-1] == 'M':
            cap = float(cap[:-1])*1000000
        else:
            cap = float(cap[:-1])

        entry = {
            'code': code,
            'price': price,
            'change_24h': change_24h,
            'change_1h': change_1h,
            'cap': cap,
        }
        save_data(entry)
        data.append(entry)

    return data

def save_whole(data):
    filename = 'data/whole'
    if not DRY_RUN:
        with open(filename, 'w') as f:
            f.write(json.dumps(data))

def load_whole():
    filename = 'data/whole'
    return yaml.safe_load(open(filename, 'r').read().decode('utf-8'))

def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.3f%s' % (num, ['', 'K', 'M', 'B', 'T', 'Q'][magnitude])

def load_marketcap_global_data():
    data = json.loads(requests.get('https://api.coinmarketcap.com/v1/global/').text)
    return data

def save_marketcap(data):
    """
    Saves market cap data and returns vector of changes direction (1 = up)
    """

    filename = 'data/marktcap'
    timestamp = calendar.timegm(time.gmtime())

    if os.path.exists(filename):
        last_line = get_last_line(filename)[0]
    else:
        last_line = '0 0 0 0 0'

    if not DRY_RUN:
        with open(filename, 'a') as f:
            f.write("%s %s %s %s\n" % (timestamp, data['total_market_cap_usd'], data['total_24h_volume_usd'], data['bitcoin_percentage_of_market_cap']))

    # getting changes direction
    vals = last_line.split()
    return (cmp(float(data['total_market_cap_usd']), float(vals[1])),
            cmp(float(data['total_24h_volume_usd']), float(vals[2])),
            cmp(float(data['bitcoin_percentage_of_market_cap']), float(vals[3])))


#
# visualzation functions
#


def colorize_number(number):
    if number.startswith('-'):
        return colored(number, 'red')
    else:
        return colored(number, 'green')

def colorize_direction(direction):
    if direction == 1:
        return Fore.GREEN + '↑' + Style.RESET_ALL
    elif direction == -1:
        return Fore.RED + '↓' + Style.RESET_ALL
    else:
        return Style.DIM + '=' + Style.RESET_ALL

def generate_spark(code, number_of_ticks=11):
    filename = 'data/%s' % code
    lines = get_last_line(filename, number_of_ticks)
    vals = [ float(x.split()[1]) for x in lines ]
    return spark.spark(vals)

def colorize_entries(entries, f_currency):

    data = []

    for rank, entry in enumerate(entries):
        code = entry['code']
        price = f_currency(entry['price'])
        change_24h = entry['change_24h']
        change_1h = entry['change_1h']
        cap = f_currency(entry['cap'])

        spark = generate_spark(code)

        change_24h  = colorize_number("%.2f%%" % change_24h)
        change_1h   = colorize_number("%.2f%%" % change_1h)
        code        = colored(code, 'cyan')
        price       = colored(to_precision(price, 6), 'cyan')
        cap         = human_format(cap)

        data.append([rank+1, code, price, change_24h, change_1h, cap, spark])

    return data

def colorize_frame(s):
    output = []
    for line in s.splitlines():
        line = line.decode('utf-8')\
                .replace(u'lqqqq', Style.DIM + u'lqqqq')\
                .replace(u'tqqqq', Style.DIM + u'tqqqq')\
                .replace(u'mqqqq', Style.DIM + u'mqqqq')\
                .replace(u'x', Style.DIM + u'x' + Style.RESET_ALL)\
                .replace(u'qqqqk', u'qqqqk' + Style.RESET_ALL)\
                .replace(u'qqqqu', u'qqqqu' + Style.RESET_ALL)\
                .replace(u'qqqqj', u'qqqqj' + Style.RESET_ALL)\
                .encode('utf-8')

        output.append(line)
    return "\n".join(output)

if len(sys.argv) == 1:
    currency = 'USD'
else:
    currency = sys.argv[1]
currency_symbol = currencies.SYMBOL.get(currency, '')

def convert_to_currency(currency, amount):
    return currencies.get_currency_rate_usd(currency)*amount
c = lambda x: convert_to_currency(currency, x)

if FETCH:
    marketcap_global_data = load_marketcap_global_data()
    data_text = get_data_text()
    data = parse_data(get_data_text())
    timestamp_now = "%s UTC" % datetime.datetime.utcnow()
    whole_data = {
        'data': data,
        'marketcap_global_data': marketcap_global_data,
        'timestamp_now': timestamp_now,
    }
    save_whole(whole_data)
else:
    whole_data = load_whole()
    marketcap_global_data = whole_data['marketcap_global_data']
    data = whole_data['data']
    timestamp_now = whole_data['timestamp_now']


market_cap_direction, vol_24h_direction, btc_dominance_direction = save_marketcap(marketcap_global_data)
marktcap_spark = generate_spark('marktcap', number_of_ticks=49)


#
# that's everything we need to save (and to load later)
#

market_cap = locale.format(
                "%d",
                int(c(marketcap_global_data['total_market_cap_usd'])),
                grouping=True)
market_cap = currency_symbol + market_cap
market_cap += ' ' + colorize_direction(market_cap_direction)

vol_24h = locale.format(
                "%d",
                int(c(marketcap_global_data['total_24h_volume_usd'])),
                grouping=True)
vol_24h = currency_symbol + vol_24h
vol_24h += ' ' + colorize_direction(vol_24h_direction)

btc_dominance = '%2.1f%%' % marketcap_global_data['bitcoin_percentage_of_market_cap']
btc_dominance += ' ' + colorize_direction(btc_dominance_direction)

header = ['Rank', 'Coin', 'Price (%s)' % currency, 'Change (24H)', 'Change (1H)', 'Market Cap (%s)' % currency, 'Spark (1H)']
header_c = [ colored(x, 'yellow') for x in header ]

rows = colorize_entries(data, c)
table = SingleTable([header_c] + rows)
table.inner_row_border = True

HEADER = HEADER.replace('Z'*48, marktcap_spark)

print colored("\n".join(HEADER.splitlines()[1:]) + "\n", 'green')
print "Market Cap: %s\n24h Vol: %s\nBTC Dominance: %s" % (market_cap, vol_24h, btc_dominance)
print colorize_frame(table.table)
print Fore.WHITE + Style.DIM + "%s" % timestamp_now  + Style.RESET_ALL
print 
print NEW_FEATURE
print FOLLOW_ME + GITHUB_BUTTON

