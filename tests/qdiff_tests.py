__author__ = 'Kal Ahmed'

import os
import unittest
import shutil
import git
from quince.core.qdiff import generate_diffs
from quince.core.qassert import assert_quad
from quince.core.repo import QUINCE_DEFAULT_GRAPH_IRI
from testutils import with_rw_repo, TestBase


class QDiffTests(TestBase):

    @with_rw_repo('HEAD')
    def test_diff_working_tree_and_head(self, repo):
        assert_quad('http://example.org/person/bob', 'http://xmlns.com/foaf/0.1/knows',
                    'http://example.org/person/alice', QUINCE_DEFAULT_GRAPH_IRI)
        print('After assert')
        generate_diffs()
