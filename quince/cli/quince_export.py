__author__ = 'Kal Ahmed'

from sys import stdout

from rdflib.util import guess_format
from quince.core.repo import QUINCE_DEFAULT_GRAPH_IRI
import quince.core.qexport as core_export
from quince.cli import pprint
from quince.core.exceptions import QuinceNoSerializerException

def parser(subparsers):
    """
    Add a parser for the export subcommand

    :param subparsers: The list of quince subcommand parsers
    :return: None
    """
    export_parser = subparsers.add_parser(
        'export',
        help='export RDF data from the Quince repository'
    )
    export_parser.add_argument('-g', '--graph',
                               help='the IRI of the graph to export from. The special value "default" specifies the'
                                    'default graph. If no graphs are specified, then all graphs are exported.',
                               action='append')
    export_parser.add_argument('-f', '--format',
                               help='specify the RDF format to use for the export. Overrides the default format'
                                    'determined by the filename extension.')
    export_parser.add_argument('filename',
                               help='the path to the file to export to. If the file exists, it will be'
                                    'overwritten. The file extension is used to determine the syntax'
                                    'for the export. To see a list of the supported formats use the'
                                    'command "quince help formats".')
    export_parser.set_defaults(func=main)


def main(args):
    output_stream = open(args.filename, 'wb') if args.filename else stdout
    if args.graph:
        graphs = list(map((lambda g: ('<' + QUINCE_DEFAULT_GRAPH_IRI + '>') if g == 'default' else ('<' + g + '>')),
                          args.graph))
    else:
        graphs = None
    output_format = args.format
    if output_format is None:
        if args.filename is not None:
            output_format = guess_format(args.filename)
        else:
            output_format = "nquads"
    try:
        core_export.export(output_stream, output_format, graphs)
    except QuinceNoSerializerException:
        pprint.err("No serializer available for the specified file extension or output format")
    finally:
        if args.filename:
            output_stream.close()