import gevent
from gevent.wsgi import WSGIServer
from gevent.queue import Queue
from gevent.monkey import patch_all
from gevent.subprocess import Popen, PIPE, STDOUT
patch_all()

import sys
import os
import glob
import re
import random
import string
import collections
import time
import json
import hashlib

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname('__file__')))
sys.path.append("%s/lib/" % MYDIR)
import currencies_names
import calculator

import view
import coins_names

from globals import error, ANSI2HTML
from buttons import TWITTER_BUTTON, GITHUB_BUTTON, GITHUB_BUTTON_FOOTER

INTERNAL_TOPICS = [":help", ":currencies", ":coins"]

def show_currencies():
    return "\n".join(["%-6s %s" % (x, currencies_names.CURRENCY_NAME[x]) for x in currencies_names.SUPPORTED_CURRENCIES]) + "\n"

def show_coins():
    return "\n".join(["%-6s %s" % (x,y) for (x,y) in coins_names.COIN_NAMES]) + "\n"

def get_internal(topic):
    if topic == ':currencies':
        return show_currencies()

    if topic == ':coins':
        return show_coins()

    if topic in INTERNAL_TOPICS:
        return open(os.path.join(MYDIR, "share", topic[1:]+".txt"), "r").read()

    return ""

def get_digest(data):
    return hashlib.sha1(json.dumps(data, sort_keys=True)).hexdigest()
 
def get_cmd_output(hostname, topic, request_options):

    digest = get_digest({'h':hostname, 't': topic, 'r': request_options})

    cache_file = '%s/cache/%s' % (MYDIR, digest)
    if os.path.exists(cache_file):
        return open(cache_file).read().decode('utf-8')
    #elif hostname == 'rate.sx' and topic == ':firstpage' and os.path.exists(cache_file):
    #    return open(cache_file).read().decode('utf-8')
    else:
        currency = hostname.lower()
        if currency.endswith('.rate.sx'):
            currency = currency[:-8].upper()

        if currency == 'COIN':
            return "Use YOUR COIN instead of COIN in the query: for example btg.rate.sx, xvg.rate.sx, eth.rate.sx and so on\nTry:\n curl btg.rate.sx\n curl xvg.rate.sx\n curl xrb.rate.sx\n"

        if currency not in currencies_names.SUPPORTED_CURRENCIES \
            and currency not in currencies_names.CRYPTO_CURRENCIES + ['coin']:
            currency = 'USD'

        if topic != ':firstpage':
            try:
                answer = calculator.calculate(topic.upper(), currency)
            except ValueError, e:
                return "ERROR: %s\n" % e

            if answer is not None:
                open(cache_file, 'w').write(str(answer)+"\n")
                return "%s\n" % answer
            else:
                return "ERROR: Can't parse your query: %s\n" % topic

        cmd = ["%s/ve/bin/python" % MYDIR, "%s/bin/show_data.py" % MYDIR, currency, topic]

    config = request_options
    config['currency'] = currency
    answer = view.show(config)

    open(cache_file, 'w').write(answer)
    #p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    #answer = p.communicate()[0]
    return answer.decode('utf-8')

def rewrite_aliases(word):
    if word == ':bash.completion':
        return ':bash_completion'
    return word

def html_wrapper(data):
    p = Popen([ "bash", ANSI2HTML, "--palette=xterm", "--bg=dark" ],  stdin=PIPE, stdout=PIPE, stderr=PIPE)
    data = data.encode('utf-8')
    stdout, stderr = p.communicate(data)
    if p.returncode != 0:
        error(stdout + stderr)
    return stdout.decode('utf-8')

def cmd_wrapper(query, hostname=None, request_options=None, html=False):

    # 
    # at the moment, we just remove trailing slashes
    # so queries python/ and python are equal
    #
    query = query.rstrip('/')

    query = rewrite_aliases(query)

    if query in INTERNAL_TOPICS:
        result = get_internal(query)
    else:
        result = get_cmd_output(hostname, query, request_options)

    if html:
        result = "\n".join(result.splitlines()[:-1])
        result = result + "\n$"
        result = html_wrapper(result)
        title = "<title>rate.sx</title>"
        result = re.sub("<head>", "<head>" + title, result)
        if not request_options.get('quiet'):
            result = result.replace('</body>', TWITTER_BUTTON + GITHUB_BUTTON + GITHUB_BUTTON_FOOTER + '</body>')

    return result

