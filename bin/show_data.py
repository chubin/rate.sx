#!/usr/bin/python
# vim: encoding=utf-8

"""
command line terminal rate.sx client
"""

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import os
MYDIR = os.path.abspath(os.path.dirname(os.path.dirname('__file__')))
sys.path.append("%s/lib/" % MYDIR)

import view

if __name__ == '__main__':
    config = {
        'number_of_ticks': 12,
        'number_of_coins': int(os.environ.get('NUMBER_OF_COINS', 10)),
        'currency': 'USD',
    }
    if len(sys.argv) > 1:
        config['currency'] = sys.argv[1]
    sys.stdout.write(view.show(config))

