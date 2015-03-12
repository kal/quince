__author__ = 'Kal Ahmed'

from quince.core import qimport as core_import
from quince.core.exceptions import QuinceParseException, QuinceNoParserException
from quince.cli import pprint


def parser(subparsers):
    """Add a parser for this command to the subparsers."""
    import_parser = subparsers.add_parser(
        'import',
        help='import RDF data from one or more files into the Quince repository'
    )
    import_parser.set_defaults(func=main)
    import_parser.add_argument('-g', '--default-graph', help='the IRI of the default graph to import into')
    import_parser.add_argument('filename', help='the path to the files to be imported', nargs='+')


def main(args):
    for file in args.filename:
        try:
            core_import.import_file(file, args.default_graph)
            pprint.msg("'{0}' - OK".format(file))
        except QuinceParseException as e:
            pprint.err("'{0}' - Parser Error: {1}".format(file, e.parser_msg))
        except QuinceNoParserException:
            pprint.err("'{0}' - No parser available for files with this file extension".format(file))



