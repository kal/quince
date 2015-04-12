__author__ = 'Kal Ahmed'

import unittest

from quince.core.qdiff import generate_diffs, SparqlDiffList
from quince.core.qassert import assert_quad, retract_quad
from quince.core.repo import QUINCE_DEFAULT_GRAPH_IRI
from testutils import TestBase, with_rw_repo


class QDiffTests(TestBase):

    @with_rw_repo('HEAD')
    def test_diff_working_tree_and_head_single_insert(self, repo):
        assert_quad('http://example.org/person/bob', 'http://xmlns.com/foaf/0.1/knows',
                    'http://example.org/person/alice', QUINCE_DEFAULT_GRAPH_IRI)
        diffs = generate_diffs()
        self.assertEqual(1, len(diffs.insertions))
        self.assertEqual('<http://example.org/person/bob> <http://xmlns.com/foaf/0.1/knows> ' \
                         '<http://example.org/person/alice> <' + QUINCE_DEFAULT_GRAPH_IRI + '> .',
                         diffs.insertions[0])

    @with_rw_repo('HEAD')
    def test_diff_working_tree_and_head_single_delete(self, repo):
        retract_quad('http://example.org/person/alice', 'http://xmlns.com/foaf/0.1/knows',
                     'http://example.org/person/bob', QUINCE_DEFAULT_GRAPH_IRI)
        diffs = generate_diffs()
        self.assertEqual(0, len(diffs.insertions))
        self.assertEqual(1, len(diffs.deletions))
        self.assertEqual('<http://example.org/person/alice> <http://xmlns.com/foaf/0.1/knows> ' \
                         '<http://example.org/person/bob> <' + QUINCE_DEFAULT_GRAPH_IRI + '> .',
                         diffs.deletions[0])

    @with_rw_repo('HEAD')
    def test_diff_working_tree_with_multiple_resource_edits(self, repo):
        assert_quad('http://example.org/person/bob', 'http://xmlns.com/foaf/0.1/knows',
                    'http://example.org/person/alice', QUINCE_DEFAULT_GRAPH_IRI)
        retract_quad('http://example.org/person/alice', 'http://xmlns.com/foaf/0.1/knows',
                     'http://example.org/person/bob', QUINCE_DEFAULT_GRAPH_IRI)
        diffs = generate_diffs()
        self.assertEqual(1, len(diffs.insertions))
        self.assertEqual(1, len(diffs.deletions))

    @with_rw_repo('HEAD')
    def test_diff_working_tree_with_named_commit(self, repo):
        assert_quad('http://example.org/person/bob', 'http://xmlns.com/foaf/0.1/knows',
                    'http://example.org/person/alice', QUINCE_DEFAULT_GRAPH_IRI)
        repo.index.commit('Bob knows Alice')
        retract_quad('http://example.org/person/alice', 'http://xmlns.com/foaf/0.1/knows',
                     'http://example.org/person/bob', QUINCE_DEFAULT_GRAPH_IRI)
        # Compared to HEAD there should just be one deletion
        diffs = generate_diffs()
        self.assertEqual(0, len(diffs.insertions))
        self.assertEqual(1, len(diffs.deletions))
        # Compared to HEAD's parent, there should be one insertion and one deletion
        diffs = generate_diffs(['HEAD^'])
        self.assertEqual(1, len(diffs.insertions))
        self.assertEqual(1, len(diffs.deletions))


class SparqlDiffListTests(unittest.TestCase):
    def test_single_addition_yields_only_insert_data(self):
        diff = SparqlDiffList()
        diff.add("+<http://example.org/s> <http://example.org/p> <http://example.org/o> <http://example.org/g> .")
        self.assertTrue(diff.any())
        self.assertEqual(1, len(diff))
        diff_str = diff.to_string()
        self.assertFalse("DELETE DATA" in diff_str)
        self.assertTrue("INSERT DATA" in diff_str)
        self.assertEqual("INSERT DATA {\n"
                         "GRAPH <http://example.org/g> {\n"
                         "<http://example.org/s> <http://example.org/p> <http://example.org/o> .\n"
                         "}\n"
                         "}", diff_str)

    def test_single_deletion_yields_only_delete_data(self):
        diff = SparqlDiffList()
        diff.add("-<http://example.org/s> <http://example.org/p> <http://example.org/o> <http://example.org/g> .")
        self.assertTrue(diff.any())
        self.assertEqual(1, len(diff))
        diff_str = diff.to_string()
        self.assertFalse("INSERT DATA" in diff_str)
        self.assertTrue("DELETE DATA" in diff_str)
        self.assertEqual("DELETE DATA {\n"
                         "GRAPH <http://example.org/g> {\n"
                         "<http://example.org/s> <http://example.org/p> <http://example.org/o> .\n"
                         "}\n"
                         "}", diff_str)

    def test_multiple_insertions_in_same_graph_yields_single_graph_clause(self):
        diff = SparqlDiffList()
        diff.add("+<http://example.org/s> <http://example.org/p> <http://example.org/o> <http://example.org/g> .")
        diff.add("+<http://example.org/s2> <http://example.org/p> <http://example.org/o> <http://example.org/g> .")
        self.assertTrue(diff.any())
        self.assertEqual(2, len(diff))
        self.assertEqual("INSERT DATA {\n"
                         "GRAPH <http://example.org/g> {\n"
                         "<http://example.org/s> <http://example.org/p> <http://example.org/o> .\n"
                         "<http://example.org/s2> <http://example.org/p> <http://example.org/o> .\n"
                         "}\n"
                         "}", diff.to_string())

    def test_insertions_in_different_graphs_yields_separate_graph_clauses(self):
        diff = SparqlDiffList()
        diff.add("+<http://example.org/s> <http://example.org/p> <http://example.org/o> <http://example.org/g> .")
        diff.add("+<http://example.org/s2> <http://example.org/p> <http://example.org/o> <http://example.org/g2> .")
        self.assertTrue(diff.any())
        self.assertEqual(2, len(diff))
        self.assertIn(
            "INSERT DATA {\n"
            "GRAPH <http://example.org/g> {\n"
            "<http://example.org/s> <http://example.org/p> <http://example.org/o> .\n"
            "}", diff.to_string())
        self.assertIn(
            "GRAPH <http://example.org/g2> {\n"
            "<http://example.org/s2> <http://example.org/p> <http://example.org/o> .\n"
            "}\n"
            "}", diff.to_string())

