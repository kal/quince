__author__ = 'ahmedk'

from quince.core import qdiff as core_diff


def parser(subparsers):
    diff_parser = subparsers.add_parser(
        'diff',
        help='generate a diff report for a resource, graph or entire repository'
    )
    diff_parser.set_defaults(func=main)
    diff_parser.add_argument('-r', '--resource',
                             help='Report only diffs on RDF statements with the specified resource as a subject.')
    diff_parser.add_argument('-g', '--graph',
                             help='Report only diffs on RDF statements from the specified named graph.')
    diff_parser.add_argument('-u', '--update',
                             help='Generate the report as a series of SPARQL Update commands',
                             action='set_true')


def main(args):
    diffs = core_diff.generate_diffs(args.resource, args.graph, 'sparql' if args.update else 'nquad_diff')
