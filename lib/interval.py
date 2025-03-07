"""
Interval functions.

Supported intervals:

    LENGTH
    DATETIME
    DATETIME..[DATETIME]
    DATETIME+LENGTH
    DATETIME-LENGTH
    DATETIME+-LENGTH

If DATETIME is not specified, then NOW and - is implied:

    NOW-LENGTH

LENGTH has the following format:

    {NUMBER INTERVAL_SPECIFICATOR}+

INTERVAL_SPECIFICATOR is one of the following:

    s   Second
    m   Minute
    h   Hour
    d   Day (24 hours)
    w   week
    M   month (30 days)
    y   year (365 days)

Length examples:

    10m
    1h30m
    10d
    3w

DATETIME can be specified in any parsable format
(parsed by dateparser).

If DATETIME specifies some long interval (say day or month),
then this interval is considered as the resulting interval.
"""

import calendar
import datetime
import re
from dateutil.relativedelta import relativedelta
import dateparser
from typing import Tuple

INTERVAL_LENGTH = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 24 * 3600,
    "w": 7 * 24 * 3600,
    "M": 30 * 24 * 3600,
    "y": 365 * 24 * 3600,
}


def _epoch(dt_tuple: datetime.datetime) -> int:
    return calendar.timegm(dt_tuple.timetuple())


def _parse_datetime(date_time: str) -> datetime.datetime:
    if date_time == "":
        return datetime.datetime.now()
    return dateparser.parse(date_time)


def parse_datetime(date_time: str, now: None=None) -> int:
    """
    Parse ``date_time``, return time in seconds since EPOCH.
    """
    if date_time == "" and now is not None:
        return now

    parsed = _parse_datetime(date_time)
    if parsed:
        return _epoch(parsed)
    return None


def from_secs(secs: int) -> str:
    """
    Convert number of seconds ``secs`` into interval description.

    >>> from_secs(10)
    '10s'
    >>> from_secs(60)
    '1m'
    >>> from_secs(3600)
    '1h'
    >>> from_secs(3660)
    '1h1m'

    """

    result = ""
    for name, size in sorted(INTERVAL_LENGTH.items(), key=lambda x: -x[1]):
        number_of_subintervals = secs // size
        secs = secs % size
        if number_of_subintervals:
            result += f"{number_of_subintervals}{name}"
    return result


def parse_length(length: str) -> int:
    """
    Parse ``length``` and return parsed length interval (in seconds)
    or None if length can't be parsed.

    >>> parse_length('1m')
    60
    >>> parse_length('1h1m')
    3660
    >>> parse_length('1')
    >>> parse_length('1hX1m')
    >>> parse_length('1d')
    86400
    >>> parse_length('2M')
    5184000
    """

    sum_ = 0
    joined = ""
    letters = "".join(INTERVAL_LENGTH.keys())
    for number, int_spec in re.findall(f"([0-9]+)([{letters}])", length):
        joined += number + int_spec
        try:
            sum_ += int(number) * INTERVAL_LENGTH[int_spec]
        except KeyError:
            return None

    # if there were some skipped characters,
    # it was not a correct interval specification,
    # return None
    if joined != length:
        return None

    return sum_


def parse_interval(
    interval_string: str, now: None=None
) -> Tuple[int, int]:  # pylint: disable=too-many-branches,too-many-return-statements
    """
    Parse ``interval_string`` and return a pair of timestamps
    in seconds since EPOCH

    >>> parse_interval('1h', now=3600)
    (0, 3600)
    >>> a, b = parse_interval('2018-01-10+1h'); b-a
    3600
    >>> a, b = parse_interval('2018-01-10+-1h'); b-a
    7200
    >>> a, _ = parse_interval('2018-01-10-1h'); _, b = parse_interval('2018-01-10+1h'); b-a
    7200
    >>> a, b = parse_interval('2018-01-01'); b-a
    86400
    >>> a, b = parse_interval('Jan,01'); b-a
    86400
    >>> a, b = parse_interval('2018-01'); b-a
    2678400
    >>> a, b = parse_interval('Jan'); b-a
    2678400
    """

    #
    # Parsing DATETIME..[DATETIME]
    #
    separator_index = interval_string.rfind("..")
    if separator_index != -1:
        first = interval_string[:separator_index]
        second = interval_string[separator_index + 2 :]
        return parse_datetime(first), parse_datetime(second)

    #
    # Parsing DATETIME+-[LENGTH]
    #         DATETIME+[LENGTH]
    #         DATETIME-[LENGTH]
    #
    operator = None
    separator_index = interval_string.rfind("+-")
    if separator_index != -1:
        operator = "+-"
    else:
        separator_index = interval_string.rfind("+")
        if separator_index != -1:
            operator = "+"
        else:
            separator_index = interval_string.rfind("-")
            if separator_index != -1:
                # we accept this string only if LENGTH can be parsed as LENGTH
                if parse_length(interval_string[separator_index + 1 :]):
                    operator = "-"

    if operator is not None:
        first = interval_string[:separator_index]
        second = interval_string[separator_index + len(operator) :]

        length = parse_length(second)
        if length is None:
            raise SyntaxError(f"Can't parse interval: {second}")

        given_date = parse_datetime(first, now=now)
        if given_date is None:
            raise SyntaxError(f"Can't parse date/time: {first}")

        if operator == "-":
            return given_date - length, given_date
        if operator == "+":
            return given_date, given_date + length
        if operator == "+-":
            return given_date - length, given_date + length

    #
    # Parsing LENGTH
    #
    length = parse_length(interval_string)
    if length is not None:
        now = parse_datetime("", now=now)
        return now - length, now

    #
    # Parsing DATETIME
    #
    parsed = _parse_datetime(interval_string)
    if parsed is not None:
        if dateparser.parse(
            interval_string, settings={"RELATIVE_BASE": datetime.datetime(1, 1, 1)}
        ) != dateparser.parse(
            interval_string, settings={"RELATIVE_BASE": datetime.datetime(1, 1, 2)}
        ):
            delta = relativedelta(months=1)
        elif parsed.hour == 0:
            delta = relativedelta(days=1)
        elif parsed.minute == 0:
            delta = relativedelta(hours=1)

        return _epoch(parsed), _epoch(parsed + delta)

    return None, None
