# vim: encoding=utf-8

"""
This file can be imported for currency related functions.
It is also used as a program to gather currency data.

Currencies data is gathered every five minutes using cron (see crontab).
Data is stored in CURRENCIES_FILE.

At the moment data is stored in a plain file.
It will be moved to a mongodb server later.

Exported functions:

    get_currency_rate_btc
    get_currency_rate_usd
    get_currency_rate_to_usd
    get_currency_rate

At the moment functions are returning only current values
"""

SUPPORTED_CURRENCIES = [
    "AUD", "BRL", "CAD", "CHF", "CLP", "CNY", "CZK", "DKK", "EUR", "GBP",
    "HKD", "HUF", "IDR", "ILS", "INR", "JPY", "KRW", "MXN", "MYR", "NOK",
    "NZD", "PHP", "PKR", "PLN", "RUB", "SEK", "SGD", "THB", "TRY", "TWD",
    "ZAR"
]

SYMBOL = {
    'USD': '$',
    'AUD': '$',
    'CAD': '$',
    'CHF': 'CHF ',
    'CNY': '¥',
    'EUR': '€',
    'GBP': '£',
    'IDR': '₹',
    'INR': '₹',
    'ILS': '₪',
    'JPY': '¥',
    'KRW': '₩',
    'RUB': '₽',
    'MXN': '$',
    'MYR': 'MR ',
    'NZD': '$',
    'PHP': '₱',
    'PLN': 'zł',
    'SEK': 'kr',
    'SGD': '$',
    'THB': '฿',
    'TRY': '₺',
    'TWD': 'NT$',
    'ZAR': 'R ',
}

CURRENCY_NAME = {
    "AUD": "Australian dollar",
    "BRL": "Brazilian real",
    "CAD": "Canadian dollar",
    "CHF": "Swiss franc",
    "CLP": "Chilean peso",
    "CNY": "Chinese yuan",
    "CZK": "Czech koruna",
    "DKK": "Danish krone",
    "EUR": "Euro",
    "GBP": "Pound sterling",
    "HKD": "Hong Kong dollar",
    "HUF": "Hungarian forint",
    "IDR": "Indonesian rupiah",
    "ILS": "Israeli shekel",
    "INR": "Indian rupee",
    "JPY": "Japanese yen",
    "KRW": "South Korean won",
    "MXN": "Mexican peso",
    "MYR": "Malaysian ringgit",
    "NOK": "Norwegian krone",
    "NZD": "New Zealand dollar",
    "PHP": "Philippine peso",
    "PKR": "Pakistani rupee",
    "PLN": "Polish zloty",
    "RUB": "Russian ruble",
    "SEK": "Swedish krona",
    "SGD": "Singapore dollar",
    "THB": "Thai baht",
    "TRY": "Turkish lira",
    "TWD": "New Taiwan dollar",
    "ZAR": "South African rand"
}

CRYPTO_CURRENCIES = [
    'BTC', 'ETH', 'XRP', 'BCH', 'ADA', 'LTC', 'XEM', 'XLM', 'MIOTA', 'NEO',
    'EOS', 'DASH', 'XMR', 'TRX', 'BTG', 'ETC', 'ICX', 'QTUM', 'LSK', 'XRB',
    'XTZ', 'MKR',
]

def currency_name(symbol):
    """
    Return full name of the currency ``symbol``
    """
    return CURRENCY_NAME.get(symbol, "")
