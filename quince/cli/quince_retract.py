__author__ = 'Kal Ahmed'

from quince.cli import pprint

from quince.core.repo import QUINCE_DEFAULT_GRAPH_IRI
from quince.core import qassert
from quince.core.exceptions import QuinceMultiException


def parser(subparsers):
    """Adds the assert command parser"""
    retract_parser = subparsers.add_parser(
        'retract',
        help='Removes all statements matching a pattern from the quince repository'
    )
    retract_parser.add_argument('subject',
                                help='The subject of the statement. '
                                     'May be an absolute IRI, a safe CURIE or a * wildcard.')
    retract_parser.add_argument('predicate',
                                help='The predicate of the statement. '
                                     'May be an absolute IRI, a safe CURIE or a * wildcard.',
                                nargs='?')
    retract_parser.add_argument('object',
                                help='The object of the statement. '
                                     'May be a quoted literal, absolute IRI, a safe CURIE or a * wildcard.',
                                nargs='?')
    retract_parser.add_argument('graph', nargs='?',
                                help='The named graph to add the statement to. '
                                     'May be an absolute IRI, a safe CURIE or a * wildcard')
    retract_parser.set_defaults(graph=QUINCE_DEFAULT_GRAPH_IRI, func=main)


def main(args):
    try:
        retracted = qassert.retract_quad(args.subject, args.predicate, args.object, args.graph)
    except QuinceMultiException as e:
        for inner in e.inner_exceptions:
            pprint.err(inner.message)
        return False
    pprint.msg('Retracted {0} quad{1}.'.format(len(retracted), '' if len(retracted) == 1 else 's'))
    for r in retracted:
        pprint.msg(r)


