__author__ = 'Kal Ahmed'

import os
from pygit2 import init_repository as git_init

from . import repo as repo_lib

# Return codes
SUCCESS = 1
NOTHING_TO_INIT = 2


def init_cwd():
    """Makes the current working directory a Quince repository"""
    if repo_lib.git_dir():
        return NOTHING_TO_INIT
    git_init(os.getcwd())
    return SUCCESS