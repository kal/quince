__author__ = 'Kal Ahmed'

import configparser
import hashlib
import os
import re
import unittest

from rdflib import Namespace, URIRef, Literal

from quince.core.repo import QuinceStore, QUINCE_DEFAULT_GRAPH_IRI, LRUCache, init, FileEntry
import quince.core.exceptions as quince_exceptions
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


class InitTests(unittest.TestCase):

    def test_init_file_structure(self):
        root_path = testutils.ensure_empty_dir('init_test')
        init(root_path)
        self.assertTrue(os.path.exists(os.path.join(root_path, '.git')), 'Expected a .git directory to be created')
        self.assertTrue(os.path.exists(os.path.join(root_path, '.quince')),
                        'Expected a .quince directory to be created')
        self.assertTrue(os.path.exists(os.path.join(root_path, '.quince', 'config')),
                        'Expected a config file inside the .quince directory')


class StoreTestsBase(unittest.TestCase):
    DEFAULT_GRAPH = URIRef(QUINCE_DEFAULT_GRAPH_IRI)

    def set_root(self, root):
        self.root = root

    def get_file_path(self, resource_n3):
        h = hashlib.sha1(resource_n3.encode()).hexdigest()
        return os.path.join(self.root, h[:2], h)

    def assert_file_for_subject(self, resource_n3):
        f = self.get_file_path(resource_n3) + ".nqo"
        self.assertTrue(os.path.exists(f), 'Did not find expected file at {0} for resource {1}'.format(f, resource_n3))
        return f


class QuinceStoreTests(StoreTestsBase):

    def setUp(self):
        self.set_root(testutils.ensure_empty_dir('QuinceStoreTests'))
        init(self.root)
        self.store = QuinceStore(self.root)

    def test_assert_quad_creates_nqo_file(self):
        self.store.assert_quad(EG.s1, EG.p1, EG.o1)
        self.store.flush()
        s1_out = self.assert_file_for_subject(EG.s1.n3())
        s1_out_lines = testutils.get_lines(s1_out)
        expected_nquad = testutils.make_nquad(EG.s1, EG.p1, EG.o1, StoreTestsBase.DEFAULT_GRAPH)
        self.assertIn(expected_nquad, s1_out_lines)

    def test_assert_two_quads_in_same_file(self):
        self.store.assert_quad(EG.s2, EG.p1, EG.o1)
        self.store.assert_quad(EG.s2, EG.p1, EG.o2)
        self.store.flush()

        s2_out = self.assert_file_for_subject(EG.s2.n3())
        s2_out_lines = testutils.get_lines(s2_out)
        self.assertIn(testutils.make_nquad(EG.s2, EG.p1, EG.o1, StoreTestsBase.DEFAULT_GRAPH), s2_out_lines)
        self.assertIn(testutils.make_nquad(EG.s2, EG.p1, EG.o2, StoreTestsBase.DEFAULT_GRAPH), s2_out_lines)

    def test_add_namespace(self):
        self.store.add_namespace('eg', 'http://example.org/')
        config = configparser.ConfigParser()
        config.read([os.path.join(self.root, '.quince', 'config')])
        self.assertTrue(config.has_section('Namespaces'))
        self.assertTrue(config.has_option('Namespaces', 'eg'))
        self.assertEqual('http://example.org/', config.get('Namespaces', 'eg'))
        self.assertEqual('http://example.org/', self.store.expand_ns_prefix('eg'))

    def test_remove_namespace(self):
        self.store.add_namespace('eg', 'http://example.org/')
        self.store.add_namespace('foaf', 'http://xmlns.com/foaf/0.1/')
        self.store.remove_namespace('eg')
        config = configparser.ConfigParser()
        config.read([os.path.join(self.root, '.quince', 'config')])
        self.assertTrue(config.has_section('Namespaces'))
        self.assertFalse(config.has_option('Namespaces', 'eg'))
        self.assertTrue(config.has_option('Namespaces', 'foaf'))

    def test_cannot_overwrite_existing_namespace(self):
        self.store.add_namespace('eg', 'http://example.org/')
        with self.assertRaises(quince_exceptions.QuinceNamespaceExistsException):
            self.store.add_namespace('eg', 'http://example.com/')

    def test_cannot_expand_undefined_namespace(self):
        self.store.add_namespace('eg', 'http://example.org')
        with self.assertRaises(quince_exceptions.QuinceNoSuchNamespaceException):
            self.store.expand_ns_prefix('ex')


class MatchQuadTests(StoreTestsBase):
    def setUp(self):
        self.set_root(testutils.ensure_empty_dir('MatchQuadTests'))
        self.store = QuinceStore(self.root)
        self.store.assert_quad(EG.s1, EG.p1, EG.o1, EG.g1)
        self.store.assert_quad(EG.s1, EG.p1, Literal("123"), EG.g1)
        self.store.flush()
        self.s1_out = self.assert_file_for_subject(EG.s1.n3())

    def test_match_quad_exact(self):
        matches = list(self.store.match_quads_in_file(self.s1_out,
                                                      self.store.make_nquad_pattern(EG.s1, EG.p1, EG.o1, EG.g1)))
        expected_nquad = testutils.make_nquad(EG.s1, EG.p1, EG.o1, EG.g1)
        self.assertEqual(1, len(matches))
        self.assertIn(expected_nquad, matches)

    def test_match_quad_wildcard(self):
        matches = list(self.store.match_quads_in_file(self.s1_out, self.store.make_nquad_pattern(EG.s1, '*', '*', '*')))
        self.assertEqual(2, len(matches))

    def test_remove_lines(self):
        store_file = FileEntry(self.s1_out)
        p = self.store.make_nquad_pattern(EG.s1, '*', '*', '*')
        removed = store_file.remove_matches(re.compile(self.store.make_nquad_pattern(EG.s1, '*', '*', '*')))
        self.assertEqual(2, len(removed))


class LruCacheTests(unittest.TestCase):
    def test_insert(self):
        cache = LRUCache(capacity=10)
        cache.set('foo', 1)
        self.assertTrue('foo' in cache)
        self.assertFalse('bar' in cache)
        self.assertEqual(1, cache.get('foo'))
        self.assertIsNone(cache.get('bar'))

    def test_remove(self):
        cache = LRUCache(capacity=10)
        cache.set('foo', 1)
        self.assertTrue('foo' in cache)
        cache.drop('foo')
        self.assertFalse('foo' in cache)
        self.assertIsNone(cache.get('foo'))

if __name__ == '__main__':
    unittest.main()
