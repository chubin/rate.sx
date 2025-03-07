# encoding: utf-8

"""
Helper functions used in view_ansi.py and in draw.py
"""

from colorama import Fore, Style
from termcolor import colored


def colorize_number(number):
    """
    If number is negative make it red, otherwise green
    """
    if not isinstance(number, str):
        number = str(number)
    if number.startswith("-"):
        return colored(number, "red")
    return colored(number, "green")


def colorize_direction(direction):
    """
    Green for the up direction,
    gray for the same, and red for the down direction
    """
    if direction == 1:
        return Fore.GREEN + "↑" + Style.RESET_ALL
    if direction == -1:
        return Fore.RED + "↓" + Style.RESET_ALL
    return Style.DIM + "=" + Style.RESET_ALL
