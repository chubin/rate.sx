"""
visualization of data for ANSI terminal
"""

import sys
import os
import locale

from terminaltables import WindowsTable

# Other useful tables:
#  GithubFlavoredMarkdownTable, SingleTable, DoubleTable, PorcelainTable
from colorama import Fore, Style
from termcolor import colored

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname("__file__")))
sys.path.append(f"{MYDIR}/lib/")

# pylint: disable=wrong-import-position
from to_precision import to_precision
import spark
import currencies_names
from ansi_utils import colorize_number, colorize_direction
from globals import MSG_FOLLOW_ME, MSG_NEW_FEATURE, MSG_GITHUB_BUTTON

# pylint: enable=wrong-import-position

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")


HEADER = r"""
                                                            X          _               Y
                                                            X _ _ __ _| |_ ___  ____ __Y
                                                            X| '_/ _` |  _/ -_)(_-< \ /Y     
__ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZX__________|_| \__,_|\__\___()__/_\_\_____Y
 '           '           '           '           '                                           """

HEADER = HEADER.replace("X", "\033[33m").replace("Y", "\033[32m")

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
    return f"{num:.3f}{['', 'K', 'M', 'B', 'T', 'Q'][magnitude]}"


def _colorize_entries(entries):
    """
    Colorize table <entries>
    """

    data = []

    for rank, entry in enumerate(entries):
        code = entry["code"]
        price = entry["price"]
        change_24h = entry["change_24h"]
        change_1h = entry["change_1h"]
        cap = entry["cap"]
        s_spark = spark.spark(entry["spark"])

        if change_24h != "-":
            change_24h = colorize_number(f"{change_24h:.2f}%")

        if change_1h != "-":
            change_1h = colorize_number(f"{change_1h:.2f}%")

        code = colored(code, "cyan")
        price = colored(to_precision(price, 6), "cyan")
        cap = human_format(cap)

        data.append([str(rank + 1), code, price, change_24h, change_1h, cap, s_spark])

    return data


def _colorize_frame(s_frame):
    """
    Colorize frame in string s_frame
    """

    output = []
    for line in s_frame.splitlines():
        line = (
            line.replace("lqqqq", Style.DIM + "lqqqq")
            .replace("tqqqq", Style.DIM + "tqqqq")
            .replace("mqqqq", Style.DIM + "mqqqq")
            .replace("x", Style.DIM + "x" + Style.RESET_ALL)
            .replace("qqqqk", "qqqqk" + Style.RESET_ALL)
            .replace("qqqqu", "qqqqu" + Style.RESET_ALL)
            .replace("qqqqj", "qqqqj" + Style.RESET_ALL)
        )

        line = (
            line.replace("┌────", Style.DIM + "┌────")
            .replace("├────", Style.DIM + "├────")
            .replace("└────", Style.DIM + "└────")
            .replace("│", Style.DIM + "│" + Style.RESET_ALL)
            .replace("────┐", "────┐" + Style.RESET_ALL)
            .replace("────┤", "────┤" + Style.RESET_ALL)
            .replace("────┘", "────┘" + Style.RESET_ALL)
        )

        output.append(line)
    return "\n".join(output)


#
# that's everything we need to save (and to load later)
#


def print_table(
    currency, data, directions, marktcap_spark, config
):  # pylint: disable=too-many-locals
    """
    Generate main table. Use specified <currency> as the main unit.
    """

    market_cap_direction, vol_24h_direction, btc_dominance_direction = directions

    currency_symbol = currencies_names.SYMBOL.get(currency, "")
    currency_suffix = ""
    if currency_symbol == "":
        currency_suffix = " " + currency

    market_cap = locale.format(
        "%d", int(data["marketcap_global_data"]["total_market_cap_usd"]), grouping=True
    )
    market_cap = currency_symbol + market_cap + currency_suffix
    market_cap += " " + colorize_direction(market_cap_direction)

    vol_24h = locale.format(
        "%d", int(data["marketcap_global_data"]["total_24h_volume_usd"]), grouping=True
    )
    vol_24h = currency_symbol + vol_24h + currency_suffix
    vol_24h += " " + colorize_direction(vol_24h_direction)

    btc_dominance = (
        f"{data['marketcap_global_data']['bitcoin_percentage_of_market_cap']:2.1f}%"
    )
    btc_dominance += " " + colorize_direction(btc_dominance_direction)

    header = [
        "Rank",
        "Coin",
        f"Price ({currency})",
        "Change (24H)",
        "Change (1H)",
        f"Market Cap ({currency})",
        "Spark (1H)",
    ]
    table_class = WindowsTable
    table = table_class(
        [[colored(x, "yellow") for x in header]] + _colorize_entries(data["data"])
    )
    table.inner_row_border = True

    header = HEADER.replace("Z" * 48, marktcap_spark)

    output = []
    output += [colored("\n".join(header.splitlines()[1:]) + "\n", "green")]
    output += [
        f"Market Cap: {market_cap}\n24h Vol: {vol_24h}\nBTC Dominance: {btc_dominance}"
    ]
    output += [_colorize_frame(table.table)]
    output += [Fore.WHITE + Style.DIM + f"{data['timestamp_now']}" + Style.RESET_ALL]
    output += [""]

    if not config.get("no-follow-line"):
        output += [MSG_NEW_FEATURE]
        output += [MSG_FOLLOW_ME + MSG_GITHUB_BUTTON]

    return "\n".join(output) + "\n"
