__author__ = 'Kal Ahmed'

import logging

import git

from quince.core.repo import QuinceStore, qdir, git_dir, QUINCE_DIR


def sort_all():
    store = QuinceStore(qdir())
    store.sort_quads()
    return True


def sort_modified(since=None):
    g = git.Repo(git_dir())
    log = logging.getLogger('quince')
    if since is None:
        head_commit = g.head.commit
        diff_index = head_commit.diff(paths=QUINCE_DIR)
    else:
        since_commit = g.commit(since)
        diff_index = since_commit.diff(paths=QUINCE_DIR)
    path_list = []
    for d in diff_index:
        if not d.deleted_file:
            path_list.append(d.b_blob.path)
    if len(path_list) == 0:
        log.warn('No locally modified files found in the quince repository.')
        return
    log.debug('Checking sort order for {0} file{1}'.format(len(path_list), '' if len(path_list) == 1 else 's'))
    store = QuinceStore(qdir())
    store.sort_quads(path_list)
    return True
