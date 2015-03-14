__author__ = 'Kal Ahmed'

SUCCESS = 0
IOERROR = 2

from quince.core import serializers
from quince.core.repo import QuinceStore, qdir


def export(output_stream, output_format, graphs):
    """
    Export the contents of the Quince repository

    :param output_stream: The stream to write to
    :param output_format: The RDF syntax to export
    :param graphs: A list of graph IRIs or None to export all graphs
    :return: 0 on success, non-zero on error
    """
    store = QuinceStore(qdir(), None)
    serializer = serializers.get_serializer(output_format, output_stream, "utf-8")
    for line in store.all_quads(graphs):
        serializer.on_line(line)