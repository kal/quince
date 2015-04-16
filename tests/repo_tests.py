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

    @testutils.with_working_dir()
    def test_init_file_structure(self, root_path):
        init(root_path, init_git=True)
        self.assertTrue(os.path.exists(os.path.join(root_path, '.git')), 'Expected a .git directory to be created')
        self.assertTrue(os.path.exists(os.path.join(root_path, '.quince')),
                        'Expected a .quince directory to be created')
        self.assertTrue(os.path.exists(os.path.join(root_path, '.quince', 'config')),
                        'Expected a config file inside the .quince directory')


class StoreTestsBase(testutils.TestBase):
    DEFAULT_GRAPH = URIRef(QUINCE_DEFAULT_GRAPH_IRI)

    def get_file_path(self, store, resource_n3):
        h = hashlib.sha1(resource_n3.encode()).hexdigest()
        return os.path.join(store.root, h[:2], h)

    def assert_file_for_subject(self, store, resource_n3):
        f = self.get_file_path(store, resource_n3) + ".nqo"
        self.assertTrue(os.path.exists(f), 'Did not find expected file at {0} for resource {1}'.format(f, resource_n3))
        return f


class QuinceStoreTests(StoreTestsBase):

    @testutils.with_store("HEAD")
    def test_assert_quad_creates_nqo_file(self, store):
        store.assert_quad(EG.s1, EG.p1, EG.o1)
        store.flush()
        s1_out = self.assert_file_for_subject(store, EG.s1.n3())
        s1_out_lines = testutils.get_lines(s1_out)
        expected_nquad = testutils.make_nquad(EG.s1, EG.p1, EG.o1, StoreTestsBase.DEFAULT_GRAPH)
        self.assertIn(expected_nquad, s1_out_lines)

    @testutils.with_store("HEAD")
    def test_assert_two_quads_in_same_file(self, store):
        store.assert_quad(EG.s2, EG.p1, EG.o1)
        store.assert_quad(EG.s2, EG.p1, EG.o2)
        store.flush()

        s2_out = self.assert_file_for_subject(store, EG.s2.n3())
        s2_out_lines = testutils.get_lines(s2_out)
        self.assertIn(testutils.make_nquad(EG.s2, EG.p1, EG.o1, StoreTestsBase.DEFAULT_GRAPH), s2_out_lines)
        self.assertIn(testutils.make_nquad(EG.s2, EG.p1, EG.o2, StoreTestsBase.DEFAULT_GRAPH), s2_out_lines)

    @testutils.with_store("HEAD")
    def test_add_namespace(self, store):
        store.add_namespace('eg', 'http://example.org/')
        config = configparser.ConfigParser()
        config.read([os.path.join(store.root, 'config')])
        self.assertTrue(config.has_section('Namespaces'))
        self.assertTrue(config.has_option('Namespaces', 'eg'))
        self.assertEqual('http://example.org/', config.get('Namespaces', 'eg'))
        self.assertEqual('http://example.org/', store.expand_ns_prefix('eg'))

    @testutils.with_store("HEAD")
    def test_remove_namespace(self, store):
        store.add_namespace('eg', 'http://example.org/')
        store.add_namespace('foaf', 'http://xmlns.com/foaf/0.1/')
        store.remove_namespace('eg')
        config = configparser.ConfigParser()
        config.read([os.path.join(store.root, 'config')])
        self.assertTrue(config.has_section('Namespaces'))
        self.assertFalse(config.has_option('Namespaces', 'eg'))
        self.assertTrue(config.has_option('Namespaces', 'foaf'))

    @testutils.with_store("HEAD")
    def test_cannot_overwrite_existing_namespace(self, store):
        store.add_namespace('eg', 'http://example.org/')
        with self.assertRaises(quince_exceptions.QuinceNamespaceExistsException):
            store.add_namespace('eg', 'http://example.com/')

    @testutils.with_store("HEAD")
    def test_cannot_expand_undefined_namespace(self, store):
        store.add_namespace('eg', 'http://example.org')
        with self.assertRaises(quince_exceptions.QuinceNoSuchNamespaceException):
            store.expand_ns_prefix('ex')

    @testutils.with_store("HEAD")
    def test_add_remote(self, store):
        store.add_remote('test', 'http://example.org/test/sparql')
        section = store.config['Remote "test"']
        self.assertIsNotNone(section)
        self.assertEqual('http://example.org/test/sparql', section['endpoint'])

    @testutils.with_store("HEAD")
    def test_cannot_add_remote_with_duplicate_name(self, store):
        store.add_remote('test', 'http://example.org/test/sparql')
        with self.assertRaises(quince_exceptions.QuinceRemoteExistsException):
            store.add_remote('test', 'http://test.org/sparql')
        section = store.config['Remote "test"']
        self.assertIsNotNone(section)
        self.assertEqual('http://example.org/test/sparql', section['endpoint'])

    @testutils.with_store("HEAD")
    def test_remove_remote(self, store):
        store.add_remote('test', 'http://example.org/test/sparql')
        store.add_remote('test2', 'http://test.org/sparql')
        store.remove_remote('test')
        with self.assertRaises(KeyError):
            section = store.config['Remote "test"']
        section = store.config['Remote "test2"']
        self.assertIsNotNone(section)

    @testutils.with_store("HEAD")
    def test_remove_nonexistent_remote_raises_nosuchremoteexception(self, store):
        store.add_remote('test', 'http://example.org/test/sparql')
        with self.assertRaises(quince_exceptions.QuinceNoSuchRemoteException):
            store.remove_remote('test2')


class MatchQuadTests(StoreTestsBase):

    def init_store(self, store):
        self.store = store
        self.store.assert_quad(EG.s1, EG.p1, EG.o1, EG.g1)
        self.store.assert_quad(EG.s1, EG.p1, Literal("123"), EG.g1)
        self.store.flush()
        self.s1_out = self.assert_file_for_subject(store, EG.s1.n3())

    @testutils.with_store("HEAD")
    def test_match_quad_exact(self, store):
        self.init_store(store)
        matches = list(self.store.match_quads_in_file(self.s1_out,
                                                      self.store.make_nquad_pattern(EG.s1, EG.p1, EG.o1, EG.g1)))
        expected_nquad = testutils.make_nquad(EG.s1, EG.p1, EG.o1, EG.g1)
        self.assertEqual(1, len(matches))
        self.assertIn(expected_nquad, matches)

    @testutils.with_store("HEAD")
    def test_match_quad_wildcard(self, store):
        self.init_store(store)
        matches = list(self.store.match_quads_in_file(self.s1_out, self.store.make_nquad_pattern(EG.s1, '*', '*', '*')))
        self.assertEqual(2, len(matches))

    @testutils.with_store("HEAD")
    def test_remove_lines(self, store):
        self.init_store(store)
        store_file = FileEntry(self.s1_out)
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
