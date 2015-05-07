__author__ = 'Kal Ahmed'
"""Module for pretty printing Quince output."""

import copy
import logging
import sys

from clint.textui import puts, colored

# Standard output

def msg(text, p=sys.stdout.write):
    puts('# {0}'.format(text), stream=p)


def out(text, p=sys.stdout.write):
    puts(text, stream=p)

# Error messages

def err(text):
    msg(text, p=sys.stderr.write)


class ConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        my_record = copy.copy(record)
        if record.levelno >= logging.ERROR:
            my_record.msg = colored.red(record.msg)
        elif record.levelno >= logging.WARNING:
            my_record.msg = colored.yellow(record.msg)
        elif record.levelno >= logging.INFO:
            my_record.msg = colored.green(record.msg)
        logging.StreamHandler.emit(self, my_record)
