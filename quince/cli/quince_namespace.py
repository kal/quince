__author__ = 'Kal Ahmed'

from quince.cli import pprint
from quince.core import qnamespace
from quince.core import exceptions


def parser(subparsers):
    """Adds the namespace command parser to the given subparsers object"""
    ns_parser = subparsers.add_parser(
        'namespace',
        help='Manage namespace prefix mappings.'
    )
    ns_parser.set_defaults(func=lambda a: main(a, ns_parser))
    ns_subparsers = ns_parser.add_subparsers(dest='ns_subcmd')
    add_parser = ns_subparsers.add_parser(
        'add',
        help='Add a namespace prefix mapping.',
    )
    add_parser.add_argument('prefix', help='The namespace prefix to be added')
    add_parser.add_argument('iri', help='The IRI that the namespace prefix is mapped to')
    add_parser.set_defaults(subfunc=add)
    remove_parser = ns_subparsers.add_parser(
        'remove',
        help='Remove a namespace prefix mapping.'
    )
    remove_parser.add_argument('prefix', help='The namespace prefix to be removed')
    remove_parser.set_defaults(subfunc=remove)
    list_parser = ns_subparsers.add_parser(
        'list',
        help='List all currently defined namespace prefix mappings.'
    )
    list_parser.set_defaults(subfunc=show)


def main(args, p):
    if args.ns_subcmd is None:
        p.print_help()
        return False
    else:
        return args.subfunc(args)


def add(args):
    """
    Processes the namespace add subcmd
    :param args:
    :return:
    """
    try:
        qnamespace.add(args.prefix, args.iri)
        # Allow IRI to be specified with or without the <> delimiters
        if args.iri.startswith('<') and args.iri.endswith('>'):
            args.iri = args.iri[1:-1]
        pprint.msg('{0}: <{1}>'.format(args.prefix, args.iri))
    except exceptions.QuinceNamespaceExistsException:
        pprint.err('A mapping already exists for the namespace prefix "{0}".'.format(args.prefix))


def remove(args):
    """
    Processes the namespace remove subcmd
    :param args:
    :return:
    """
    qnamespace.remove(args.prefix)


def show(args):
    """
    Processes the namespace list subcmd
    :param args:
    :return:
    """
    mappings = qnamespace.get_mappings()
    for k, v in mappings.items():
        pprint.out('{0}: <{1}>'.format(k, v))