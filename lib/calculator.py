import datetime
import re
import time

import currencies
import interval

"""

Currencies calculator.

Exports:

    calculate()

"""

# historical rates older than that (before the requested time) are not used
MAX_RATE_AGE = 24 * 3600


def _split_currency(s):
    factor = 1
    if s.startswith("+"):
        s = s[1:]
        factor = 1
    if s.startswith("-"):
        s = s[1:]
        factor = -1

    m = re.match(r"([0-9]+)([A-Z]*)$", s)
    if m:
        amount, currency = m.groups(1)
        amount = float(amount)
        return factor * amount, currency

    m = re.match(r"([0-9]+(?:\.[0-9]+))([A-Z]*)$", s)
    if m:
        amount, currency = m.groups(1)
        amount = float(amount)
        return factor * amount, currency

    return None, s


def _parse_query(q):
    q = q.replace(" ", "").replace("+", " +").replace("-", " -")
    parts = [_split_currency(x) for x in q.split()]

    result = parts
    return result


def _parse_timestamp(interval_string):
    """
    Return the timestamp of the closing rate of ``interval_string``
    (any interval specification supported by interval.py),
    or None if the interval reaches the present (the latest rates are used then).
    """

    try:
        _, time_end = interval.parse_interval(interval_string)
    except (SyntaxError, OverflowError):
        time_end = None

    if time_end is None:
        raise ValueError(f"Invalid time interval specification: {interval_string}")

    if time_end > time.time():
        return None

    # the end of the interval is exclusive
    return time_end - 1


def _get_rate_to_usd(currency, timestamp):
    try:
        return currencies.get_rate_to_usd(
            currency, timestamp=timestamp, max_age=MAX_RATE_AGE
        )
    except ValueError:
        if timestamp is None:
            raise

    # raises ValueError if the currency is not known at all
    currencies.get_rate_to_usd(currency)

    date = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
    date = date.strftime("%Y-%m-%d %H:%M")
    raise ValueError(f"No data for {currency} at {date} UTC")


def calculate(q, currency="USD"):
    """
    Calculate the (crypto)currencies expression ``q`` in ``currency``.
    ``q`` can be followed by @INTERVAL: then the closing rates
    of the interval are used, e.g. 0.1BTC@2021-03-01.
    Return None if ``q`` is not a calculator expression.
    """

    expression, _, interval_string = q.partition("@")

    parsed_query = _parse_query(expression.upper())
    if not parsed_query or any(x is None for x, y in parsed_query):
        return None

    timestamp = None
    if interval_string:
        timestamp = _parse_timestamp(interval_string)

    parsed_query = [(x, _get_rate_to_usd(y, timestamp)) for x, y in parsed_query]
    if any(y is None for x, y in parsed_query):
        return None

    result = sum(x * y for x, y in parsed_query)
    if currency == "USD":
        return result

    conversion_rate = _get_rate_to_usd(currency, timestamp)
    if conversion_rate is None:
        return None

    return result / conversion_rate
