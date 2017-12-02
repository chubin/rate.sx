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

DRY_RUN = False

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

def get_data_text():
    cmd = ["/home/igor/rate.sx/bin/cmd-data"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return stdout

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

def parse_data(text):

    lines = text.splitlines()[3:]
    header = ['Rank', 'Coin', 'Price (USD)', 'Change (24H)', 'Change (1H)', 'Market Cap (USD)', 'Spark (1H)']
    header_c = [ colored(x, 'yellow') for x in header ]

    data = [ header_c ]
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
            cap = float(cap[:-1])
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
        spark = generate_spark(code)

        change_24h  = colorize_number("%.2f%%" % change_24h)
        change_1h   = colorize_number("%.2f%%" % change_1h)
        code        = colored(code, 'cyan')
        price       = colored(to_precision(price, 6), 'cyan')
        cap         = str(cap) + 'B'


        rank += 1
        data.append([rank, code, price, change_24h, change_1h, cap, spark])

    return data

def load_marketcap_global_data():
    data = json.loads(requests.get('https://api.coinmarketcap.com/v1/global/').text)
    return data

def colorize_frame(s):
    output = []
    for line in s.splitlines():
        #print "%s" % ",".join(x for x in line)
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



marketcap_global_data = load_marketcap_global_data()
market_cap_direction, vol_24h_direction, btc_dominance_direction = save_marketcap(marketcap_global_data)
marktcap_spark = generate_spark('marktcap', number_of_ticks=49)

data_text = get_data_text()
data = parse_data(get_data_text())

market_cap = locale.format(
                "%d",
                int(marketcap_global_data['total_market_cap_usd']),
                grouping=True)
market_cap = '$' + market_cap
market_cap += ' ' + colorize_direction(market_cap_direction)

vol_24h = locale.format(
                "%d",
                int(marketcap_global_data['total_24h_volume_usd']),
                grouping=True)
vol_24h = '$' + vol_24h
vol_24h += ' ' + colorize_direction(vol_24h_direction)

btc_dominance = '%2.1f%%' % marketcap_global_data['bitcoin_percentage_of_market_cap']
btc_dominance += ' ' + colorize_direction(btc_dominance_direction)

table = SingleTable(data)
table.inner_row_border = True

HEADER = HEADER.replace('Z'*48, marktcap_spark)

print colored("\n".join(HEADER.splitlines()[1:]) + "\n", 'green')
print "Market Cap: %s\n24h Vol: %s\nBTC Dominance: %s" % (market_cap, vol_24h, btc_dominance)
print colorize_frame(table.table)
print Fore.WHITE + Style.DIM + "%s" % datetime.datetime.utcnow() + " UTC" + Style.RESET_ALL
print 
print NEW_FEATURE
print FOLLOW_ME + GITHUB_BUTTON

