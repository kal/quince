__author__ = 'ahmedk'

import os
import shutil
import sys
import tempfile
import unittest

import git
from git.compat import string_types

from quince.core.qimport import import_file
from quince.core.init import init_cwd
from quince.core.repo import QuinceStore, QUINCE_DIR

INIT_DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'foaf_sample.nt'))


def ensure_empty_dir(path):
    p = os.path.join('tmp', path)
    if os.path.isdir(p):
        shutil.rmtree(p, onerror=_rmtree_onerror)
    os.makedirs(p)
    return p


def get_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()


def make_nquad(s, p, o, g):
    return "{0} {1} {2} {3} .\n".format(s.n3(), p.n3(), o.n3(), g.n3())


def _rmtree_onerror(func, fullpath, exc_info):
    """
    Handle the case on Windows where readonly files
    cannot be deleted by os.remove by setting it to
    mode 777 then retry deletion
    """
    if os.name != 'nt':
        raise()
    os.chmod(fullpath, 0o777)
    func(fullpath)


def with_working_dir():
    def argument_passer(func):
        def directory_creator(self):
            working_dir = tempfile.mktemp(func.__name__)
            prev_cwd = os.getcwd()
            os.makedirs(working_dir)
            os.chdir(working_dir)
            try:
                try:
                    return func(self, working_dir)
                except:
                    print("Keeping temp dir after failure: {0}".format(working_dir), file=sys.stderr)
                    working_dir = None
                    raise
            finally:
                os.chdir(prev_cwd)
                if working_dir is not None:
                    shutil.rmtree(working_dir, onerror=_rmtree_onerror)
        directory_creator.__name__ = func.__name__
        return directory_creator
    return argument_passer


def with_rw_repo(working_tree_ref):
    assert isinstance(working_tree_ref, string_types), "Decorator requires ref name for working checkout"

    def argument_passer(func):
        def repo_creator(self):
            repo_dir = tempfile.mktemp(func.__name__)
            rw_repo = self.rorepo.clone(repo_dir)
            prev_cwd = os.getcwd()
            os.chdir(rw_repo.working_dir)
            try:
                try:
                    return func(self, rw_repo)
                except:
                    print("Keeping repo after failure: {0}".format(repo_dir), file=sys.stderr)
                    repo_dir = None
                    raise
            finally:
                os.chdir(prev_cwd)
                rw_repo.git.clear_cache()
                if repo_dir is not None:
                    shutil.rmtree(repo_dir, onerror=_rmtree_onerror)
        repo_creator.__name__ = func.__name__
        return repo_creator
    return argument_passer


def with_store(working_tree_ref):
    assert isinstance(working_tree_ref, string_types), "Decorator requires ref name for working checkout"

    def argument_passer(func):
        def repo_creator(self):
            repo_dir = tempfile.mktemp(func.__name__)
            rw_repo = self.rorepo.clone(repo_dir)
            prev_cwd = os.getcwd()
            os.chdir(rw_repo.working_dir)
            store = QuinceStore(os.path.join(rw_repo.working_dir, QUINCE_DIR))
            try:
                try:
                    return func(self, store)
                except:
                    print("Keeping repo after failure: {0}".format(repo_dir), file=sys.stderr)
                    repo_dir = None
                    raise
            finally:
                os.chdir(prev_cwd)
                rw_repo.git.clear_cache()
                if repo_dir is not None:
                    shutil.rmtree(repo_dir, onerror=_rmtree_onerror)
        repo_creator.__name__ = func.__name__
        return repo_creator
    return argument_passer



class TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo_dir = tempfile.mktemp(cls.__name__)
        ro_repo = git.Repo.init(repo_dir, mkdir=True)
        prev_cwd = os.getcwd()
        os.chdir(ro_repo.working_dir)
        try:
            init_cwd()
            import_file(INIT_DATA)
            ro_repo.index.commit(message='Initial import')
        finally:
            os.chdir(prev_cwd)
        cls.rorepo = ro_repo

    @classmethod
    def tearDownClass(cls):
        cls.rorepo.git.clear_cache()
        cls.rorepo.git = None