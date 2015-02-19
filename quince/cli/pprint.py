__author__ = 'Kal Ahmed'
"""Module for pretty printing Quince output."""

import sys

from clint.textui import puts

# Standard output


def msg(text, p=sys.stdout.write):
    puts('# {0}'.format(text), stream=p)


# Error messages


def err(text):
    msg(text, p=sys.stderr.write)