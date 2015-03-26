__author__ = 'ahmedk'

import argparse
from quince.core import qdiff as core_diff
from quince.cli import pprint

def parser(subparsers):
    diff_parser = subparsers.add_parser(
        'diff',
        help='generate a diff report for a resource, graph or entire repository'
    )
    diff_parser.set_defaults(func=main)
    diff_parser.add_argument('-s', '--subject',
                             help='Report only diffs on RDF statements with the specified resource as a subject.')
    diff_parser.add_argument('-g', '--graph',
                             help='Report only diffs on RDF statements from the specified named graph.')
    diff_parser.add_argument('-u', '--update',
                             help='Generate the report as a series of SPARQL Update commands',
                             action='set_true')
    diff_parser.add_argument('commit',
                             help='Reference to the commit(s) to be diffed',
                             nargs=argparse.REMAINDER)


def main(args):
    diffs = core_diff.generate_diffs(args.commit, args.resource, args.graph, 'sparql' if args.update else 'nquad_diff')
    for d in diffs:
        pprint.out(d)