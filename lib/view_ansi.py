# vim: encoding=utf-8

"""
visualization of data for ANSI terminal
"""

import sys
import os
import locale

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

from terminaltables import WindowsTable, PorcelainTable, GithubFlavoredMarkdownTable, SingleTable, DoubleTable
from colorama import Fore, Back, Style 
from termcolor import colored

MYDIR = os.path.abspath(os.path.dirname( os.path.dirname('__file__') ))
sys.path.append("%s/lib/" % MYDIR)
from to_precision import to_precision
import spark
import currencies_names


HEADER = r"""
                                                            X          _               Y
                                                            X _ _ __ _| |_ ___  ____ __Y
                                                            X| '_/ _` |  _/ -_)(_-< \ /Y     
__ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZX__________|_| \__,_|\__\___()__/_\_\_____Y
 '           '           '           '           '                                           """

HEADER = HEADER.replace('X', '\033[33m').replace('Y', '\033[32m')

FOLLOW_ME = '[Follow \033[46m\033[30m@igor_chubin\033[0m for updates]' + Style.RESET_ALL
FOLLOW_ME = Fore.CYAN + '[Follow @igor_chubin for rate.sx updates]' + Style.RESET_ALL
NEW_FEATURE = 'See ' + Fore.GREEN + 'rate.sx/:help' + Style.RESET_ALL + ' for help and disclaimer'
GITHUB_BUTTON = ' ' + '\033[100;30m' + '[github.com/chubin/rate.sx]' + Style.RESET_ALL

#
# visualzation functions
#

def human_format(num):
    """
    Convert <num> into human form (round it and add a suffix)
    """
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.3f%s' % (num, ['', 'K', 'M', 'B', 'T', 'Q'][magnitude])

def colorize_number(number):
    """
    If number is negative make it red, otherwise green
    """
    if number.startswith('-'):
        return colored(number, 'red')
    else:
        return colored(number, 'green')

def colorize_direction(direction):
    """
    Green for the up direction,
    gray for the same, and red for the down direction
    """
    if direction == 1:
        return Fore.GREEN + '↑' + Style.RESET_ALL
    elif direction == -1:
        return Fore.RED + '↓' + Style.RESET_ALL
    else:
        return Style.DIM + '=' + Style.RESET_ALL

def colorize_entries(entries):
    """
    Colorize table <entries>
    """

    data = []

    for rank, entry in enumerate(entries):
        code = entry['code']
        price = entry['price']
        change_24h = entry['change_24h']
        change_1h = entry['change_1h']
        cap = entry['cap']
        s_spark = spark.spark(entry['spark'])

        change_24h = colorize_number("%.2f%%" % change_24h)
        change_1h = colorize_number("%.2f%%" % change_1h)
        code = colored(code, 'cyan')
        price = colored(to_precision(price, 6), 'cyan')
        cap = human_format(cap)

        data.append([rank+1, code, price, change_24h, change_1h, cap, s_spark])

    return data

def colorize_frame(s_frame):
    """
    Colorize frame in string s_frame
    """

    output = []
    for line in s_frame.splitlines():
        line = line.decode('utf-8')\
                .replace(u'lqqqq', Style.DIM + u'lqqqq')\
                .replace(u'tqqqq', Style.DIM + u'tqqqq')\
                .replace(u'mqqqq', Style.DIM + u'mqqqq')\
                .replace(u'x', Style.DIM + u'x' + Style.RESET_ALL)\
                .replace(u'qqqqk', u'qqqqk' + Style.RESET_ALL)\
                .replace(u'qqqqu', u'qqqqu' + Style.RESET_ALL)\
                .replace(u'qqqqj', u'qqqqj' + Style.RESET_ALL)\
                .encode('utf-8')

        line = line.decode('utf-8')\
                .replace(u'┌────', Style.DIM + u'┌────')\
                .replace(u'├────', Style.DIM + u'├────')\
                .replace(u'└────', Style.DIM + u'└────')\
                .replace(u'│', Style.DIM + u'│' + Style.RESET_ALL)\
                .replace(u'────┐', u'────┐' + Style.RESET_ALL)\
                .replace(u'────┤', u'────┤' + Style.RESET_ALL)\
                .replace(u'────┘', u'────┘' + Style.RESET_ALL)\
                .encode('utf-8')

        output.append(line)
    return "\n".join(output)

#
# that's everything we need to save (and to load later)
#

def print_table(currency, data, directions, marktcap_spark):
    """
    Generate main table. Use specified <currency> as the main unit.
    """

    market_cap_direction, vol_24h_direction, btc_dominance_direction = directions

    currency_symbol = currencies_names.SYMBOL.get(currency, '')
    currency_suffix = ''
    if currency_symbol == '':
        currency_suffix = ' ' + currency

    market_cap = locale.format(
        "%d",
        int(data['marketcap_global_data']['total_market_cap_usd']),
        grouping=True)
    market_cap = currency_symbol + market_cap + currency_suffix
    market_cap += ' ' + colorize_direction(market_cap_direction)

    vol_24h = locale.format(
        "%d",
        int(data['marketcap_global_data']['total_24h_volume_usd']),
        grouping=True)
    vol_24h = currency_symbol + vol_24h + currency_suffix
    vol_24h += ' ' + colorize_direction(vol_24h_direction)

    btc_dominance = '%2.1f%%' % data['marketcap_global_data']['bitcoin_percentage_of_market_cap']
    btc_dominance += ' ' + colorize_direction(btc_dominance_direction)

    header = [
        'Rank',
        'Coin',
        'Price (%s)' % currency,
        'Change (24H)',
        'Change (1H)',
        'Market Cap (%s)' % currency,
        'Spark (1H)'
        ]
    table_class = WindowsTable
    table = table_class(
        [[colored(x, 'yellow') for x in header]]
        + colorize_entries(data['data']))
    table.inner_row_border = True

    header = HEADER.replace('Z'*48, marktcap_spark)

    output = []
    output += [colored("\n".join(header.splitlines()[1:]) + "\n", 'green')]
    output += ["Market Cap: %s\n24h Vol: %s\nBTC Dominance: %s" \
                % (market_cap, vol_24h, btc_dominance)]
    output += [colorize_frame(table.table)]
    output += [Fore.WHITE + Style.DIM + "%s" % data['timestamp_now']  + Style.RESET_ALL]
    output += [""]
    output += [NEW_FEATURE]
    output += [FOLLOW_ME + GITHUB_BUTTON]

    return "\n".join(output) + "\n"


