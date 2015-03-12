__author__ = 'Kal Ahmed'

from . parsers import get_parser
from . repo import qdir, QuinceStore, QuinceTripleSink
from . exceptions import QuinceParseException
NO_PARSER = 2


def import_file(file_path, default_graph=None):
    store = QuinceStore(qdir(), default_graph)
    sink = QuinceTripleSink(store)
    parser = get_parser(file_path, sink)
    if not parser:
        return NO_PARSER
    try:
        parser.parse(file_path)
    except Exception as e:
        raise QuinceParseException(file_path, e)
