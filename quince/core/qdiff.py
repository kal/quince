__author__ = 'ahmedk'

import git
from quince.core.repo import git_dir, QUINCE_DIR


def generate_diffs(resource=None, graph=None, output_format='nquad_diff'):
    g = git.Repo(git_dir())
    for diff_index in g.index.diff(None, paths=QUINCE_DIR, create_patch=True):
        print(diff_index)