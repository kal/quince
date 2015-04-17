__author__ = 'Kal Ahmed'

from quince.cli import pprint
from quince.core.repo import QuinceStore, qdir
from quince.core.exceptions import QuinceRemoteExistsException, QuinceNoSuchRemoteException


def parser(subparsers):
    remote_parser = subparsers.add_parser(
        'remote',
        help='Manage set of tracked SPARQL Update endpoints'
    )
    remote_subparsers = remote_parser.add_subparsers(dest='remote_subcmd')
    remote_add_parser = remote_subparsers.add_parser(
        'add',
        help='Add a SPARQL update endpoint for remote update'
    )
    remote_add_parser.add_argument(
        'name',
        help='The name to use for the remote')
    remote_add_parser.add_argument(
        'endpoint',
        help='The IRI of the SPARQL Update endpoint')
    remote_remove_parser = remote_subparsers.add_parser(
        'remove',
        help='Remove a remote update target'
    )
    remote_remove_parser.add_argument(
        'name',
        help='The name of the remote to be removed')
    remote_parser.set_defaults(func=main)


def main(args):
    store = QuinceStore(qdir(), None)
    if args.remote_subcmd is None:
        for remote, endpoint in store.list_remotes():
            pprint.msg('{0} {1}'.format(remote, endpoint))
    elif args.remote_subcmd == 'add':
        try:
            store.add_remote(args.name, args.endpoint)
        except QuinceRemoteExistsException:
            pprint.err('There is already a remote named "{0}"'.format(args.name))
    elif args.remote_subcmd == 'remove':
        try:
            store.remove_remote(args.name)
        except QuinceNoSuchRemoteException:
            pprint.err('No remote named "{0}"'.format(args.name))