__author__ = 'Kal Ahmed'

import argparse
import logging
import traceback

from quince.cli import pprint, quince_init, quince_import, quince_export, quince_diff, quince_namespace, \
    quince_assert, quince_retract, quince_sort
from quince.core import repo as repo_lib

VERSION = '0.1.0'

SUCCESS = 0
ERRORS_FOUND = 1
INTERNAL_ERROR = 3
NOT_IN_GL_REPO = 4


def main():
    log = logging.getLogger('quince')
    log.addHandler(pprint.ConsoleHandler())
    log.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description='Quince: RDF data management and collaboration for humans.')
    parser.add_argument(
        '--version', action='version', version='Quince Version: ' + VERSION)
    parser.add_argument(
        '-v', '--verbose', help='Produce verbose (debugging) output', action='store_true'
    )
    subparsers = parser.add_subparsers(dest='subcmd_name')
    sub_cmds = [quince_init,
                quince_import,
                quince_export,
                quince_diff,
                quince_namespace,
                quince_assert,
                quince_retract,
                quince_sort]
    for sub_cmd in sub_cmds:
        sub_cmd.parser(subparsers)

    args = parser.parse_args()
    if args.subcmd_name is None:
        parser.print_help()
        return ERRORS_FOUND

    if args.subcmd_name != 'init' and not repo_lib.git_dir():
        log.error('You are not in a Quince repository.')
        log.warn('To make this directory a repository do quince init.')
        return NOT_IN_GL_REPO

    try:
        if args.verbose:
            log.setLevel(logging.DEBUG)
        return SUCCESS if args.func(args) else ERRORS_FOUND
    except KeyboardInterrupt:
        print('\n')
        log.warn('Keyboard interrupt detected, operation aborted')
        return SUCCESS
    except:
        log.error('Sorry, something went wrong\n\n{0}'.format(traceback.format_exc()))
        return INTERNAL_ERROR
