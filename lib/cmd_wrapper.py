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

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname('__file__')))
sys.path.append("%s/lib/" % MYDIR)
import currencies
import calculator

from globals import error, ANSI2HTML
from buttons import TWITTER_BUTTON, GITHUB_BUTTON, GITHUB_BUTTON_FOOTER

INTERNAL_TOPICS = [":help"]

def get_internal(topic):
    if topic in INTERNAL_TOPICS:
        return open(os.path.join(MYDIR, "share", topic[1:]+".txt"), "r").read()

    return ""
 
def get_cmd_output(hostname, topic):
    if hostname == 'rate.sx' and topic == ':firstpage':
        cmd = ["/home/igor/rate.sx/bin/cmd", topic]
    else:
        currency = hostname.lower()
        if currency.endswith('.rate.sx'):
            currency = currency[:-8].upper()
        if currency not in currencies.SUPPORTED_CURRENCIES:
            currency = 'USD'

        if topic != ':firstpage':
            answer = calculator.calculate(topic.upper(), currency)
            if answer is not None:
                return "%s\n" % answer
            else:
                return "ERROR: Can't parse your query: %s\n" % topic

        cmd = ["/home/igor/rate.sx/ve/bin/python", "/home/igor/rate.sx/bin/collect_data_new_curr.py", currency, topic]
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    answer = p.communicate()[0]
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
        result = get_cmd_output(hostname, query)

    if html:
        result = "\n".join(result.splitlines()[:-1])
        result = result + "\n$"
        result = html_wrapper(result)
        title = "<title>rate.sx</title>"
        result = re.sub("<head>", "<head>" + title, result)
        if not request_options.get('quiet'):
            result = result.replace('</body>', TWITTER_BUTTON + GITHUB_BUTTON + GITHUB_BUTTON_FOOTER + '</body>')

    return result

