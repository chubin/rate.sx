"""
Miscelaneous utility functions
"""

import re

def remove_ansi(sometext):
    """
    Remove ANSI sequences from `sometext`
    """
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', sometext)
