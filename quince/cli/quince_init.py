__author__ = 'Kal Ahmed'

""" quince init - Create an empty repository """

import os

from quince.core import init as core_init

from . import pprint


def parser(subparsers):
    """Adds the init command parser to the given subparsers object"""
    init_parser = subparsers.add_parser(
        'init',
        help='create an empty Quince repository.'
    )
    init_parser.set_defaults(func=main)


def main(args):
    ret = core_init.init_cwd()
    if ret is core_init.NOTHING_TO_INIT:
        return False
    elif ret is core_init.SUCCESS:
        return True
    else:
        raise Exception('Unexpected return code {0}'.format(ret))