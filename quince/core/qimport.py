__author__ = 'Kal Ahmed'

import os.path
import urllib.request

from quince.core.parsers import get_parser
from quince.core.repo import qdir, QuinceStore, QuinceTripleSink, git_add_files
from quince.core.exceptions import QuinceParseException, QuinceNoParserException

SUCCESS = 0


def import_file(file_path, default_graph=None):
    store = QuinceStore(qdir(), default_graph)
    sink = QuinceTripleSink(store)
    parser = get_parser(file_path, sink)
    if not parser:
        raise QuinceNoParserException(file_path)
    try:
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                parser.parse(f)
        elif file_path.lower().startswith('http://') or file_path.lower().startswith('https://'):
            with urllib.request.urlopen(file_path) as f:
                parser.parse(f)
        else:
            raise IOError("File not found")
        store.flush()
        git_add_files()
        return SUCCESS
    except Exception as e:
        raise QuinceParseException(file_path, e)



