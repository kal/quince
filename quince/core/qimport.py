__author__ = 'Kal Ahmed'

import os.path

import git
from quince.core.parsers import get_parser
from quince.core.repo import repo_dir, qdir, QuinceStore, QuinceTripleSink
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


def git_add_files():
    """git-add .quince directory and all of its contents"""
    g = repo_dir()
    repo = git.Repo(g)
    q = os.path.relpath(qdir())
    untracked = repo.untracked_files
    quince_files = list(filter(lambda x: x.startswith(q), untracked))
    repo.index.add(quince_files)
