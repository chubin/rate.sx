#!/usr/bin/env python
# vim: set encoding=utf-8

import gevent
from gevent.wsgi import WSGIServer
from gevent.queue import Queue
from gevent.monkey import patch_all
from gevent.subprocess import Popen, PIPE, STDOUT
patch_all()

import sys
import logging
import os
import re
import requests
import socket
import subprocess
import time
import traceback
import dateutil.parser
import json

import jinja2
from flask import Flask, request, render_template, send_from_directory, send_file, make_response, redirect
app = Flask(__name__)

MYDIR = os.path.abspath(os.path.dirname( os.path.dirname('__file__') ))
sys.path.append("%s/lib/" % MYDIR)

from globals import FILE_QUERIES_LOG, LOG_FILE, TEMPLATES, STATIC, log, error

from cmd_wrapper import cmd_wrapper

if not os.path.exists(os.path.dirname(LOG_FILE)):
    os.makedirs(os.path.dirname(LOG_FILE))
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(message)s')

my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(TEMPLATES),
])
app.jinja_loader = my_loader

def is_html_needed(user_agent):
    plaintext_clients = [ 'curl', 'wget', 'fetch', 'httpie', 'lwp-request', 'python-requests']
    if any([x in user_agent for x in plaintext_clients]):
        return False
    return True

def parse_args(args):
    result = {}

    q = ""
    for key, val in args.items():
        if len(val) == 0:
            q += key
            continue

    if q is None:
        return result
    if 'T' in q:
        result['no-terminal'] = True
    if 'q' in q:
        result['quiet'] = True

    for key, val in args.items():
        if val == 'True':
            val = True
        if val == 'False':
            val = False
        result[key] = val

    return result

@app.route('/files/<path:path>')
def send_static(path):
    return send_from_directory(STATIC, path)

@app.route('/favicon.ico')
def send_favicon():
    return send_from_directory(STATIC, 'favicon.ico')

@app.route('/malformed-response.html')
def send_malformed():
    return send_from_directory(STATIC, 'malformed-response.html')

def log_query(ip, topic, user_agent):
    log_entry = "%s %s %s" % (ip, topic, user_agent)
    with open(FILE_QUERIES_LOG, 'a') as my_file:
        my_file.write(log_entry.encode('utf-8')+"\n")

@app.route("/", methods=['GET'])
@app.route("/<path:topic>", methods=["GET"])
def answer(topic = None):
    """
    Main rendering function, it processes incoming weather queries.
    Depending on user agent it returns output in HTML or ANSI format.

    Incoming data:
        request.args
        request.headers
        request.remote_addr
        request.referrer
        request.query_string
    """

    user_agent = request.headers.get('User-Agent', '').lower()
    html_needed = is_html_needed(user_agent)
    options = parse_args(request.args)

    if request.headers.getlist("X-Forwarded-For"):
       ip = request.headers.getlist("X-Forwarded-For")[0]
       if ip.startswith('::ffff:'):
           ip = ip[7:]
    else:
       ip = request.remote_addr
    if request.headers.getlist("X-Forwarded-For"):
       ip = request.headers.getlist("X-Forwarded-For")[0]
       if ip.startswith('::ffff:'):
           ip = ip[7:]
    else:
       ip = request.remote_addr


    if topic is None:
        topic = ":firstpage"

    answer = cmd_wrapper(topic, request_options=options, html=is_html_needed(user_agent))
    
    log_query(ip, topic, user_agent)
    return answer

server = WSGIServer(("", 8004), app) # log=None)
server.serve_forever()

