__author__ = 'Kal Ahmed'

import os.path
from quince.core.parsers import get_parser
from quince.core.repo import qdir, QuinceStore, QuinceTripleSink, git_add_files
from quince.core.exceptions import QuinceParseException

SUCCESS = 0
NO_PARSER = 2


def import_file(file_path, default_graph=None):
    store = QuinceStore(qdir(), default_graph)
    sink = QuinceTripleSink(store)
    parser = get_parser(file_path, sink)
    if not parser:
        return NO_PARSER
    try:
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                parser.parse(f)
            store.flush()
            git_add_files()
            return SUCCESS
        else:
            raise IOError("File not found")
    except Exception as e:
        raise QuinceParseException(file_path, e)



