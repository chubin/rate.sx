import re
import currencies

"""

Currencies calculator.

Exports:

    calculate()

"""


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


def calculate(q, currency="USD"):

    parsed_query = _parse_query(q)
    if any(x is None for x, y in parsed_query):
        return None

    parsed_query = [(x, currencies.get_rate_to_usd(y)) for x, y in parsed_query]
    if any(y is None for x, y in parsed_query):
        return None

    result = sum(x * y for x, y in parsed_query)
    if currency == "USD":
        return result

    conversion_rate = currencies.get_rate_to_usd(currency)
    if conversion_rate is None:
        return None

    return result / conversion_rate
