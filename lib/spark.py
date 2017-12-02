#vim:encoding=utf-8

import math
from termcolor import colored

def my_ceil(v):

    result = math.ceil(v)
    if result < 0:
        result -= 1
    if result == 0:
        result = 1
    return int(result)

def to_bar(x):
    bars = u'▁▂▃▅▇'
    clr = 'green'
    if x < 0:
        clr = 'red'
        x = -x
    return colored(bars[(x-1)%len(bars)], clr)


def spark(vals):
    deltas = [ y-x for (x,y) in zip(vals[:-1], vals[1:]) ]


    max_delta = max(abs(x) for x in deltas)
    mapped_deltas = [ my_ceil(x*5.0/max_delta) for x in deltas ]

    bars = [to_bar(x) for x in mapped_deltas]

    return "".join(bars).encode('utf-8')

