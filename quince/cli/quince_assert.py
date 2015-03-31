__author__ = 'Kal Ahmed'

from quince.cli import pprint

from quince.core.repo import QUINCE_DEFAULT_GRAPH_IRI
from quince.core import qassert
from quince.core.exceptions import QuinceMultiException

def parser(subparsers):
    """Adds the assert command parser"""
    assert_parser = subparsers.add_parser(
        'assert',
        help='Add a statement to the quince repository'
    )
    assert_parser.add_argument('subject',
                               help='The subject of the statement. Must be an absolute IRI or a safe CURIE.')
    assert_parser.add_argument('predicate',
                               help='The predicate of the statement. Must be an absolute IRI or a safe CURIE.')
    assert_parser.add_argument('object',
                               help='The object of the statement. Must be a quoted literal, absolute IRI '
                                    'or a safe CURIE.')
    assert_parser.add_argument('graph', nargs='?',
                               help='The named graph to add the statement to. Must be an absolute IRI or a safe CURIE')
    assert_parser.set_defaults(graph=QUINCE_DEFAULT_GRAPH_IRI, func=main)


def main(args):
    try:
        s, p, o, g = qassert.assert_quad(args.subject, args.predicate, args.object, args.graph)
    except QuinceMultiException as e:
        for inner in e.inner_exceptions:
            pprint.err(inner.message)
        return False
    pprint.msg("{0} {1} {2} {3} .".format(s.n3(), p.n3(), o.n3(), g.n3()))


