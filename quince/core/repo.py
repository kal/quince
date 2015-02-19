__author__ = 'Kal Ahmed'

import os


def git_dir():
    """Gets the path to the .git directory.

    :returns:
        The absolute path to the git directory or None if
        the current working directory is not a Git repository
    """
    cd = os.getcwd()
    ret = os.path.join(cd, '.git')
    while os.path.dirname(cd) != cd:
        if os.path.isdir(ret):
            return ret
        cd = os.path.dirname(cd)
        ret = os.path.join(cd, '.git')
    return None


def repo_dir():
    """Get the full path to the Git repo."""
    return git_dir()[:-4]