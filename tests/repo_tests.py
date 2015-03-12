__author__ = 'Kal Ahmed'

import unittest
import hashlib
import os
import re

from rdflib import Namespace, URIRef

from quince.core.repo import QuinceStore, QUINCE_DEFAULT_GRAPH_IRI

import testutils

EG = Namespace('http://example.org/')


class NQuadRegularExpressionTests(unittest.TestCase):
    def test_match_valid_ntriple_iris(self):
        self.assertTrue(re.fullmatch(QuinceStore.IRI_MATCH, '<http://example.org/s>'))

    def test_match_valid_ntriple_literal(self):
        self.assertIsNotNone(re.fullmatch(QuinceStore.LITERAL_MATCH, '"hello"'))
        self.assertIsNotNone(re.fullmatch(QuinceStore.LITERAL_MATCH,
                                          '"hello"^^<http://www.w3.org/2001/XMLSchema#string>'))
        self.assertIsNotNone(re.fullmatch(QuinceStore.LITERAL_MATCH, '"hello"@en'))
        self.assertIsNotNone(re.fullmatch(QuinceStore.LITERAL_MATCH, '"bonjour"@fr-be'))
        self.assertIsNotNone(re.fullmatch(QuinceStore.LITERAL_MATCH, '"hello \\"world\\""'))
        self.assertIsNotNone(re.fullmatch(QuinceStore.LITERAL_MATCH, '"This is a multi-line\\n'
                                                                     'literal with many quotes(\\"\\"\\"\\")\\n'
                                                                     'and two apostrophes (\'\')."'))


class StoreTestsBase(unittest.TestCase):
    DEFAULT_GRAPH = URIRef(QUINCE_DEFAULT_GRAPH_IRI)
    def assert_file_for_subject(self, resource_n3):
        f = self.get_file_path(resource_n3) + ".nqo"
        self.assertTrue(os.path.exists(f), 'Did not find expected file at {0} for resource {1}'.format(f, resource_n3))
        return f

    def assert_file_for_object(self, resource_n3):
        f = self.get_file_path(resource_n3) + ".nqi"
        self.assertTrue(os.path.exists(f), 'Did not find expected file at {0} for resource {1}'.format(f, resource_n3))
        return f


class QuinceStoreTests(StoreTestsBase):

    def setUp(self):
        self.root = testutils.ensure_empty_dir('QuinceStoreTests')
        self.store = QuinceStore(self.root)

    def test_assert_quad_creates_nqi_and_nqo_files(self):
        self.store.assert_quad(EG.s1, EG.p1, EG.o1)
        self.store.flush()

        s1_out = self.assert_file_for_subject(EG.s1.n3())
        s1_out_lines = testutils.get_lines(s1_out)
        o1_in = self.assert_file_for_object(EG.o1.n3())
        o1_in_lines = testutils.get_lines(o1_in)
        expected_nquad = testutils.make_nquad(EG.s1, EG.p1, EG.o1, StoreTestsBase.DEFAULT_GRAPH)
        self.assertIn(expected_nquad, s1_out_lines)
        self.assertIn(expected_nquad, o1_in_lines)

    def test_assert_two_quads_in_same_file(self):
        self.store.assert_quad(EG.s2, EG.p1, EG.o1)
        self.store.assert_quad(EG.s2, EG.p1, EG.o2)
        self.store.flush()

        s2_out = self.assert_file_for_subject(EG.s2.n3())
        s2_out_lines = testutils.get_lines(s2_out)
        self.assertIn(testutils.make_nquad(EG.s2, EG.p1, EG.o1, StoreTestsBase.DEFAULT_GRAPH), s2_out_lines)
        self.assertIn(testutils.make_nquad(EG.s2, EG.p1, EG.o2, StoreTestsBase.DEFAULT_GRAPH), s2_out_lines)

    def get_file_path(self, resource_n3):
        h = hashlib.sha1(resource_n3.encode()).hexdigest()
        return os.path.join(self.root, h[:2], h[2:])


class MatchQuadTests(StoreTestsBase):
    def setUp(self):
        self.root = testutils.ensure_empty_dir('MatchQuadTests')
        self.store = QuinceStore(self.root)
        self.store.assert_quad(EG.s1, EG.p1, EG.o1, EG.g1)
        self.store.assert_quad(EG.s1, EG.p1, EG.o2, EG.g1)
        self.store.flush()
        self.s1_out = self.assert_file_for_subject(EG.s1.n3())

    def test_match_quad_exact(self):
        matches = list(self.store.match_quads_in_file(self.s1_out,
                                                      self.store.make_nquad_pattern(EG.s1, EG.p1, EG.o1, EG.g1)))
        expected_nquad = testutils.make_nquad(EG.s1, EG.p1, EG.o1, EG.g1)
        self.assertEqual(1, len(matches))
        self.assertIn(expected_nquad, matches)



if __name__ == '__main__':
    unittest.main()
