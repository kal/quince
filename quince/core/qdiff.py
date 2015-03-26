__author__ = 'ahmedk'

import git
from quince.core.repo import git_dir, QUINCE_DIR


def generate_diffs(commits=None, resource=None, graph=None, output_format='nquad_diff'):
    g = git.Repo(git_dir())
    commits = commits or []
    if len(commits) == 0:
        diff_index = g.index.diff('HEAD', paths=QUINCE_DIR, create_patch=True)
    elif len(commits) == 1:
        to_commit = g.commit(commits[0])
        diff_index = g.index.diff(to_commit, paths=QUINCE_DIR, create_patch=True)
    else:
        from_commit = g.commit(commits[0])
        to_commit = g.commit(commits[1])
        diff_index = from_commit.diff(to_commit, paths=QUINCE_DIR, create_patch=True)
    for diff in diff_index:
        print(diff)