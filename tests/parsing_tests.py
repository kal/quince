__author__ = 'Kal Ahmed'

import hashlib
import unittest
from unittest.mock import Mock, MagicMock
import os
import os.path

from rdflib.plugins.parsers.ntriples import NTriplesParser
from quince.core.parsers import NQuadsParser, get_parser
from rdflib import Namespace, URIRef, Literal
from quince.core.repo import QUINCE_DEFAULT_GRAPH_IRI, QuinceTripleSink, RdflibGraphAdapter

import testutils


NS = Namespace('http://example.org/')


class QuinceParserTests(unittest.TestCase):

    def setUp(self):
        self.root = testutils.ensure_empty_dir('QuinceParserTests')

    def test_simple_parse_from_string(self):
        store = Mock()
        store.assert_quad = MagicMock()
        sink = QuinceTripleSink(store)
        p = NTriplesParser(sink)
        p.parsestring('<http://example.org/s> <http://example.org/p> <http://example.org/o> .')
        store.assert_quad.assert_called_with(NS.s, NS.p, NS.o)

    def test_simple_literal_parse(self):
        store = Mock()
        store.assert_quad = MagicMock()
        sink = QuinceTripleSink(store)
        p = NTriplesParser(sink)
        p.parsestring('<http://example.org/s> <http://example.org/p> "hello world" .')
        store.assert_quad.assert_called_with(NS.s, NS.p, Literal("hello world"))

    def test_parse_nquads(self):
        sink = Mock()
        sink.quad = MagicMock()
        p = NQuadsParser(sink)
        p.parsestring('<http://example.org/s> <http://example.org/p> <http://example.org/o> <http://example.org/g> .')

    def test_guess_format(self):
        sink = Mock()
        p = get_parser('test.nt', sink)
        self.assertIsNotNone(p)
        self.assertIsInstance(p, NTriplesParser)

if __name__ == '__main__':
    unittest.main()
