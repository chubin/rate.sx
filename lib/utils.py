"""
Miscelaneous utility functions
"""

import re


def remove_ansi(sometext):
    """
    Remove ANSI sequences from `sometext`
    """
    ansi_escape = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")
    return ansi_escape.sub("", sometext)


def remove_trailing_spaces(sometext):
    sometext = sometext.replace("\x1b(B", "")  # re_esc_b.sub("", sometext)

    re_trailing_spaces = re.compile(r" *$", re.MULTILINE)
    return re_trailing_spaces.sub("", sometext)
