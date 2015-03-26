__author__ = 'Kal Ahmed'

import os
import unittest
import shutil
import git
from quince.core.qdiff import generate_diffs
from quince.core.qimport import import_file
from quince.core.init import init_cwd
from quince.core.qassert import assert_quad
from quince.core.repo import QUINCE_DEFAULT_GRAPH_IRI

class QDiffTests(unittest.TestCase):
    def setUp(self):
        # Create a test repository
        self._work_dir = os.path.abspath(os.curdir)
        self._test_data_dir = os.path.join(os.path.dirname(os.path.abspath(os.path.relpath(__file__))), 'data')
        self._repo_dir = os.path.abspath('/tmp/quince_tests/qdiff_tests')
        self.git_repo = git.Repo.init(self._repo_dir, mkdir=True)
        try:
            os.chdir(self._repo_dir)
            init_cwd()
            import_file(os.path.join(self._test_data_dir, 'foaf_sample.nt'))
            self.git_repo.index.commit('Initial commit')
        finally:
            os.chdir(self._work_dir)

    def tearDown(self):
        # shutil.rmtree(self._repo_dir)
        pass

    def test_diff_working_tree_and_head(self):
        os.chdir(self._repo_dir)
        try:
            print('Before assert')
            generate_diffs()
            assert_quad('http://example.org/person/bob', 'http://xmlns.com/foaf/0.1/knows',
                        'http://example.org/person/alice', QUINCE_DEFAULT_GRAPH_IRI)
            print('After assert')
            generate_diffs()
        finally:
            os.chdir(self._work_dir)