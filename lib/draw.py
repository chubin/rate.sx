# encoding: utf-8

"""
 1 [X] update all coins data
 2 [X] currencies support
 3 [X] add update script to cron

 4 [X] high alignment calculation
 5 [X] low alignment calculation
 6 [X] avg
 7 [X] median
 8 [X] change (percent)
 9 [X] currency fullname
10 [X] header (human readable interval)
11 [/] left axis
12 [/] bottom axis
13 [X] date/time input
14 [X] intervals

15 [X] move to a separate module

16 [X] url support
17 [ ] terminal size
18 [ ] json output

19 [X] readme update
20 [X]  intervals
21 [X]  url
22 [X]   screenshots
23 [ ] help update

24 [ ] commit

25 [X] add nice colors
26 [X] add message about @interval
27 [X] add message about /help
28 [X] add the message to the main page
29 [X] clean up the code, remove all warnings

30 [X] support of small intervals
31 [X] output coin choice

32 [ ] fix the strange bug of diagram
33 [ ] coin position change
34 [X] add a warning if interval is truncated
35 [ ] add a warning if one of the currencies is overridden
"""
from __future__ import print_function

import sys
import datetime
import os
import re
from io import BytesIO

import diagram
from colorama import Fore, Back, Style

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname("__file__")))
sys.path.append(f"{MYDIR}/lib/")

# pylint: disable=wrong-import-position
import aggregate
import coins_names
import currencies_names
import interval
from ansi_utils import colorize_number
from to_precision import to_precision
from globals import MSG_SEE_HELP, MSG_INTERVAL

# pylint: enable=wrong-import-position

PALETTES = {
    0: {
        1: Fore.WHITE,
        2: Style.DIM,
    },
    1: {
        1: Fore.CYAN,
        2: Style.DIM,
    },
    2: {
        1: Fore.RED,
        2: Style.DIM,
    },
}

PALETTES_REVERSE = {
    0: {
        1: Back.WHITE + Fore.BLACK,
        2: Style.DIM,
    },
    1: {
        1: Back.CYAN + Fore.BLACK,
        2: Style.DIM,
    },
    2: {
        1: Back.RED + Fore.BLACK,
        2: Style.DIM,
    },
}


def _format_value(value, precision=3, show_plus=False):
    value = str(to_precision(value, precision))

    plus = ""
    if show_plus and not value.startswith("-"):
        plus = "+"

    if "e" in value:
        return plus + str(float(value)).lstrip("+")
    return plus + value.lstrip("+")


def _format_percentage(value):
    res = f"{value:.2f}%"
    if value > 0:
        res = "+" + res
    return res


class Diagram(object):  # pylint: disable=too-many-instance-attributes
    """
    Diagram drawer. Uses ``data`` (with ``meta`` and ``ticks``) as its input,
    returns formated diagram as a string (generate_diagram()) or
    prints it on the stdout (show_diagram()).
    """

    def __init__(self, data, interval_pair, options=None):
        self.data = data
        self.options = options if options is not None else {}
        self.width = self.options.get("width", 80)
        self.height = self.options.get("height", 25)
        self.palette = 0
        self.warnings = self.options.get("warnings", [])

        self.interval = interval_pair[1] - interval_pair[0]
        self.currency = self.options.get("currency" or "USD")
        self.currency_symbol = currencies_names.SYMBOL.get(self.currency)

    def _align_label(self, timestamp, label):
        """
        Align ``label`` according to its ``timestamp``
        """
        time_begin = self.data["meta"]["time_begin"]
        time_end = self.data["meta"]["time_end"]

        number_of_spaces = int(
            1.0 * self.width * (timestamp - time_begin) / (time_end - time_begin)
        )
        number_of_spaces -= len(label) // 2
        return " " * number_of_spaces + label

    def _format_time(self, timestamp, use_format=None, show_date=None, show_time=None):
        """
        Format ``timestamp`` depending on the current interval size (``self.interval``).
        If it is smaller than 24h, don't show date;
        if it is bigger than 7d, don't show time.
        If ``details`` is greater than 0, increase deails level.
        """

        if use_format is None:
            time_fmt = "%H:%M"

            if self.interval < 7 * 24 * 3600:
                date_fmt = "%a %d"
            else:
                if self.interval > 182 * 24 * 3600:
                    date_fmt = "%d %b %Y"
                else:
                    date_fmt = "%d %b"

            fmt = ""
            if self.interval >= 24 * 3600 or show_date:
                fmt = date_fmt

            if self.interval < 24 * 3600 or show_time:
                if fmt:
                    fmt += " "
                fmt += time_fmt

        else:
            fmt = use_format

        result = datetime.datetime.fromtimestamp(timestamp).strftime(fmt)
        return result

    def _format_currency(self, value):
        if not isinstance(value, str):
            value = _format_value(value)
        if self.currency_symbol:
            return f"{self.currency_symbol}{value}"
        return f"{value} {self.currency}"

    def _show_change_percentage(self):
        f_p = _format_percentage
        meta = self.data["meta"]
        change = meta["end"] - meta["begin"]
        change_percentage = 100.0 * change / meta["begin"]
        return colorize_number(
            _format_value(change, precision=5, show_plus=True)
        ), colorize_number(f_p(change_percentage))

    def _make_header(self):
        coin_symbol = self.data["meta"]["symbol"]
        coin_name = coins_names.coin_name(coin_symbol)

        meta = self.data["meta"]
        interval_name = interval.from_secs(self.interval)
        time_interval = f"{self._format_time(meta['time_begin'])} +{interval_name}"
        # self._format_time(meta['time_end'], show_date=True, show_time=True),

        output = "\n"
        if self.currency == "USD":
            output += "{-1▶ %s (%s) }{1▶}" % (coin_name, coin_symbol)
        else:
            currency_symbol = self.currency
            currency_name = currencies_names.currency_name(self.currency)
            if not currency_name:
                currency_name = coins_names.coin_name(self.currency)

            output += "{-1▶ %s (%s) to %s (%s) }{1▶}" % (
                coin_name,
                coin_symbol,
                currency_name,
                currency_symbol,
            )
        # output += u"{1%s (%s)}," % (coin_name, coin_symbol)
        output += f" {time_interval}"
        output += f" {self._show_change_percentage()[1]}\n"
        output += "\n\n"

        return output

    def _make_footer(self):

        f_f = lambda x: self._format_currency(_format_value(x, precision=5))
        f_t = lambda t: self._format_time(t, show_date=True, show_time=True)

        meta = self.data["meta"]

        output = "\n\n"
        output += (
            ""
            + "{2begin:} %s (%s)" % (f_f(meta["begin"]), f_t(meta["time_begin"]))
            + "{2 // }"
            + "{2end:} %s (%s)" % (f_f(meta["end"]), f_t(meta["time_end"]))
            + "\n"
        )
        output += (
            ""
            + "{2high:} %s (%s)" % (f_f(meta["max"]), f_t(meta["time_max"]))
            + "{2 // }"
            + "{2low:} %s (%s)" % (f_f(meta["min"]), f_t(meta["time_min"]))
            + "\n"
        )
        output += (
            ""
            + "{2avg:} %s" % f_f(meta["avg"])
            + "{2 // }"
            + "{2median:} %s" % f_f((meta["max"] + meta["min"]) / 2)
            + "{2 // }"
            + "{2change:} %s (%s)" % self._show_change_percentage()
            + "\n"
        )

        return output

    def _colorize(self, text):

        palette = PALETTES[self.palette]
        palette_reverse = PALETTES_REVERSE[self.palette]

        def _colorize_curlies_block(text):

            text = text.group()[1:-1]
            stripped = text.lstrip("0123456789-")
            color_number = int(text[: len(text) - len(stripped)])

            reverse = False
            if color_number < 0:
                color_number = -color_number
                reverse = True

            if reverse:
                stripped = palette_reverse[color_number] + stripped + Style.RESET_ALL
            else:
                stripped = palette[color_number] + stripped + Style.RESET_ALL

            return stripped

        return re.sub("{.*?}", _colorize_curlies_block, text)

    def _make_diagram(self):

        class Option(
            object
        ):  # pylint: disable=too-many-instance-attributes,too-few-public-methods
            """Diagram configuration."""

            def __init__(self):
                self.axis = False
                self.batch = None
                self.color = True
                self.encoding = None
                self.function = None
                self.height = None
                self.keys = None
                self.legend = None
                self.palette = "spectrum-reversed"
                self.reverse = None
                self.sleep = None
                self.sort_by_column = None

        diagram.PALETTE["spectrum-reversed"] = {
            0x010: diagram.PALETTE["spectrum"][0x010][::-1],
            0x100: diagram.PALETTE["spectrum"][0x100][::-1],
        }

        data = self.data

        istream = [str(x) for x in data["ticks"]]
        ostream = BytesIO()
        size = diagram.Point((self.width, self.height))
        option = Option()
        engine = diagram.AxisGraph(size, option)
        engine.consume(istream, ostream)

        meta = data["meta"]

        high_line = self._align_label(meta["time_max"], _format_value(meta["max"]))
        low_line = self._align_label(meta["time_min"], _format_value(meta["min"]))
        lines = (
            [high_line] + ostream.getvalue().decode("utf-8").splitlines() + [low_line]
        )

        output = ""
        output += "\n".join([f"  │ {x}" for x in lines])
        output += "\n  └" + "─" * 80

        return output

    def _make_messages(self):

        output = ""
        for line in self.warnings:
            output += Fore.YELLOW + f"WARNING: {line}\n" + Style.RESET_ALL

        if self.options.get("msg_interval"):
            output += MSG_INTERVAL
        else:
            output += MSG_SEE_HELP

        return output + "\n"

    def make_view(self):
        """
        Show diagram for ``self.data``
        """

        output = ""
        output += self._make_header()
        output += self._make_diagram()
        output += self._make_footer()
        output += self._make_messages()

        output = self._colorize(output)
        return output

    def print_view(self):
        """
        Show diagram on the standard output.
        """
        print(self.make_view())


def _split_query(query):

    at_index = query.find("@")
    if "@" in query:
        coin = query[:at_index]
        interval_string = query[at_index + 1 :]
    else:
        coin = query
        interval_string = "24h"

    return coin, interval_string


def _parse_query(query):

    coin, interval_string = _split_query(query)

    coin = coin.upper()
    coin2 = None
    if "/" in coin:
        coin, coin2 = coin.split("/", 1)

    if coins_names.coin_name(coin) == "" and currencies_names.currency_name(coin) == "":
        raise SyntaxError(f"Invalid coin/currency name: {coin}")

    if (
        coin2
        and coins_names.coin_name(coin2) == ""
        and currencies_names.currency_name(coin2) == ""
    ):
        raise SyntaxError(f"Invalid coin/currency name: {coin2}")

    try:
        time_begin, time_end = interval.parse_interval(interval_string)
    except OverflowError:
        # to be fixed: ranges like yesterday, today, now and so on
        raise RuntimeError(f"Wrong range specification: {interval_string}")

    if time_begin is None or time_end is None:
        raise SyntaxError(f"Invalid time interval specification: {interval_string}")

    return coin, coin2, time_begin, time_end


def get_data(query, use_currency=None):

    try:
        coin, coin2, time_begin, time_end = _parse_query(query)
    except SyntaxError as e_msg:
        raise RuntimeError(f"{e_msg}")

    # if currency is specified in the domain name (use_currency)
    # but not in the query, then we use it as the output currency
    if (
        use_currency
        and not coin2
        and (
            coins_names.coin_name(use_currency) != ""
            or currencies_names.currency_name(use_currency) != ""
        )
    ):
        coin2 = use_currency

    ticks = 80
    if coin2:
        data = aggregate.get_aggregated_pair(coin, coin2, time_begin, time_end, ticks)
    else:
        data = aggregate.get_aggregated_coin(coin, time_begin, time_end, ticks)

    return data


def view(query, use_currency=None):
    """
    Main rendering function, entry point for this module.
    Returns rendered view for the ``query``.
    If currency is specified in ``query``, it overrides ``currency``.
    If ``currency`` is not specified, USD is used.
    """

    try:
        coin, coin2, time_begin, time_end = _parse_query(query)
    except SyntaxError as e_msg:
        raise RuntimeError(f"{e_msg}")

    if not coin2 and use_currency:
        coin2 = use_currency

    data = get_data(query, use_currency=use_currency)

    if data["ticks"] == []:
        raise RuntimeError("No data found for your query. Wrong range?")

    warnings = []
    if data["meta"]["time_begin"] - time_begin > 3600 * 24:
        warnings.append(
            "for the moment, rate.sx has historical data only starting from 2018-Jan-07"
        )

    options = dict(
        width=80,
        height=25,
        msg_interval="@" not in query,
        currency=coin2 or "USD",
        warnings=warnings,
    )
    dia = Diagram(data, (time_begin, time_end), options=options)
    return dia.make_view()


def main():
    "experimenting with get_aggregated_coin()"

    if sys.argv == []:
        query = "ETH@4d"
    else:
        query = sys.argv[1]

    try:
        import json

        # sys.stdout.write(json.dumps(get_data(query)))
        sys.stdout.write(view(query))
    except RuntimeError as e_msg:
        print(f"ERROR: {e_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
