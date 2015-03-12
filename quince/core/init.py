__author__ = 'Kal Ahmed'

import os
from quince.core import repo as repo_lib

# Return codes
SUCCESS = 1
NOTHING_TO_INIT = 2


def init_cwd():
    """Makes the current working directory a Quince repository"""
    if repo_lib.git_dir():
        return NOTHING_TO_INIT
    repo_lib.init(os.getcwd())
    return SUCCESS