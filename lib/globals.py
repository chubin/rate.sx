"""
Global variables and most important functions.
"""

import logging
import os
from colorama import Fore, Style

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname('__file__')))

ANSI2HTML = os.path.join(MYDIR, "share/ansi2html.sh")

LOG_FILE = os.path.join(MYDIR, 'log/main.log')
FILE_QUERIES_LOG = os.path.join(MYDIR, 'log/queries.log')
TEMPLATES = os.path.join(MYDIR, 'share/templates')
STATIC = os.path.join(MYDIR, 'share/static')

_g = lambda x: Fore.GREEN + x + Style.RESET_ALL #pylint: disable=invalid-name
MSG_GITHUB_BUTTON = ' ' + '\033[100;30m' + '[github.com/chubin/rate.sx]' + Style.RESET_ALL
MSG_FOLLOW_ME = '[Follow \033[46m\033[30m@igor_chubin\033[0m for updates]' + Style.RESET_ALL
MSG_FOLLOW_ME = Fore.CYAN + '[Follow @igor_chubin for rate.sx updates]' + Style.RESET_ALL
MSG_NEW_FEATURE = 'See ' + _g('rate.sx/:help') + ' for help and disclaimer'
MSG_NEW_FEATURE = Fore.YELLOW + 'NEW FEATURE:' + Style.RESET_ALL \
                    + ' to see cryptocurrency exchange rate, do ' \
                    + _g('curl rate.sx/eth') + ' (or any other coin insted of ETH)'
MSG_SEE_HELP = 'See ' + _g('rate.sx/:help') + ' for help and disclaimer'
MSG_INTERVAL = ('Use '
                + _g('@')
                + ' for interval specification: '
                + _g('/btc@10d') + ', ' + _g('/eth@4w') + ', ' + _g('/xrp@January')
                + ' (more in ' + '/:help)')

def error(text):
    """
    Fatal error. Log ``text`` and produce a RuntimeException
    """
    if not text.startswith('Too many queries'):
        print text
    logging.error("ERROR %s", text)
    raise RuntimeError(text)

def log(text):
    """
    Log ``text`` to the log and on the standard out and continue
    """
    if not text.startswith('Too many queries'):
        print text
        logging.info(text)
