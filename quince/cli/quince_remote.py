__author__ = 'Kal Ahmed'

import quince.core.qremote as core_remote
from quince.cli import pprint

def parser(subparsers):
    remote_parser = subparsers.add_parser(
        'remote',
        help='Manage set of tracked SPARQL Update endpoints'
    )
    remote_subparsers = remote_parser.add_subparsers(dest='remote_subcmd')
    remote_add_parser = remote_subparsers.add_parser('add')
    remote_add_parser.add_argument('name')
    remote_add_parser.add_argument('endpoint')
    remote_remove_parser = remote_subparsers.add_parser('remove')
    remote_remove_parser.add_argument('name')
    remote_parser.set_defaults(func=main)


def main(args):
    if args.remote_subcmd is None:
        for remote, endpoint in core_remote.list():
            pprint.msg('{0} {1}'.format(remote, endpoint))
    elif args.remote_subcmd == 'add':
        core_remote.add(args.name, args.endpoint)
    elif args.remote_subcmd == 'remove':
        core_remote.remove(args.name)