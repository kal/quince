__author__ = 'Kal Ahmed'

import argparse
import traceback

from quince.cli import quince_init, pprint
from quince.core import repo as repo_lib

VERSION = '0.1.0'

SUCCESS = 0
ERRORS_FOUND = 1
INTERNAL_ERROR = 3
NOT_IN_GL_REPO = 4


def main():
    parser = argparse.ArgumentParser(description='Quince: RDF data management and collaboration for humans.')
    parser.add_argument(
        '--version', action='version', version='Quince Version: ' + VERSION)
    subparsers = parser.add_subparsers(dest='subcmd_name')
    sub_cmds = [quince_init]
    for sub_cmd in sub_cmds:
        sub_cmd.parser(subparsers)

    args = parser.parse_args()
    if args.subcmd_name != 'init' and not repo_lib.git_dir():
        pprint.err(
            'You are not in a Quince repository. To make this directory a repository '
            'do quince init.'
        )
        return NOT_IN_GL_REPO

    try:
        return SUCCESS if args.func(args) else ERRORS_FOUND
    except KeyboardInterrupt:
        print('\n')
        pprint.msg('Keyboard interrupt detected, operation aborted')
        return SUCCESS
    except:
        pprint.err('Sorry, something went wrong\n\n{0}'.format(traceback.format_exc()))
        return INTERNAL_ERROR
