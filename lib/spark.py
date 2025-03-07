# vim:encoding=utf-8

from __future__ import print_function
import math
from termcolor import colored
from typing import List


def my_ceil(v: float) -> int:
    if v < 0:
        if math.ceil(v) != v:
            v -= 1
    result = math.ceil(v)
    return int(result)


def to_bar(x: int) -> str:
    bars = "_▁▂▃▅▇"
    clr = "green"
    if x < 0:
        clr = "red"
        x = -x
    return colored(bars[x % len(bars)], clr)


def spark_numbers(vals: List[float]) -> List[int]:
    deltas = [y - x for (x, y) in zip(vals[:-1], vals[1:])]
    max_delta = max(abs(x) for x in deltas)

    if max_delta == 0:
        mapped_deltas = [0 for x in deltas]
    else:
        mapped_deltas = [my_ceil(x * 5.0 / max_delta) for x in deltas]

    return mapped_deltas


def spark(vals: List[float]) -> str:
    mapped_deltas = spark_numbers(vals)
    bars = [to_bar(x) for x in mapped_deltas]

    return "".join(bars)


if __name__ == "__main__":
    data = [1, -1, 2, -2, 3, -3, 4, -4, 5, -5]
    print(spark_numbers(data))
    print(spark(data))
