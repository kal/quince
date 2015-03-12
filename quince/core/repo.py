__author__ = 'Kal Ahmed'

import os
import re
import bisect
import collections
import hashlib
from enum import Enum

import git
import rdflib

from .exceptions import QuincePreconditionFailedException

QUINCE_DIR = '.quince'
QUINCE_DEFAULT_GRAPH_IRI = rdflib.URIRef('http://networkedplanet.com/quince/.well-known/default-graph')
NQOUT = '.nqo'
NQIN = '.nqi'


def git_dir():
    """Gets the path to the .git directory.

    :returns:
        The absolute path to the git directory or None if
        the current working directory is not a Git repository
    """
    cd = os.getcwd()
    ret = os.path.join(cd, '.git')
    while os.path.dirname(cd) != cd:
        if os.path.isdir(ret):
            return ret
        cd = os.path.dirname(cd)
        ret = os.path.join(cd, '.git')
    return None


def repo_dir():
    """Get the full path to the Git repo."""
    return git_dir()[:-4]


def qdir():
    """Get the full path to the .quince directory of the Git repo."""
    return os.path.join(repo_dir(), QUINCE_DIR)


def init(path):
    git.Repo.init(path)
    os.mkdir(os.path.join(qdir(), QUINCE_DIR))


class UpdateMode(Enum):
    ASSERT = 1
    RETRACT = 2
    EXISTS = 3
    NOT_EXISTS = 4


class QuinceTripleSink:
    def __init__(self, store, update_mode=UpdateMode.ASSERT, throw_on_failed_precondition=False):
        self.store = store
        self.update_mode = update_mode
        self.failed_preconditions = []
        self.throw_on_failed_precondition = throw_on_failed_precondition

    def quad(self, s, p, o, g):
        if self.update_mode is UpdateMode.ASSERT:
            self.store.assert_quad(s, p, o, g)
        if self.update_mode is UpdateMode.RETRACT:
            self.store.retract_quad(s, p, o, g)
        if self.update_mode is UpdateMode.EXISTS:
            if not self.store.exists(s, p, o):
                self.failed_precondition(s, p, o, g or self.store.default_graph)
        if self.update_mode is UpdateMode.NOT_EXISTS:
            if self.store.exists(s, p, o):
                self.failed_precondition(s, p, o, g or self.store.default_graph)

    def triple(self, s, p, o):
        if self.update_mode is UpdateMode.ASSERT:
            self.store.assert_quad(s, p, o)
        if self.update_mode is UpdateMode.RETRACT:
            self.store.retract_quad(s, p, o)
        if self.update_mode is UpdateMode.EXISTS:
            if not self.store.exists(s, p, o):
                self.failed_precondition(s, p, o, self.store.default_graph)
        if self.update_mode is UpdateMode.NOT_EXISTS:
            if self.store.exists(s, p, o):
                self.failed_precondition(s, p, o, self.store.default_graph)

    def failed_precondition(self, s, p, o, g):
        if self.throw_on_failed_precondition:
            raise QuincePreconditionFailedException(self.update_mode, s, p, o, g)
        self.failed_preconditions.append((self.update_mode, s, p, o, g))


class RdflibGraphAdapter(rdflib.ConjunctiveGraph):
    def __init__(self, sink):
        super().__init__()
        self.sink = sink
        self.current_context = None
        self.context_aware = True
        self._Graph__store = self
        self._Graph__identifier = rdflib.URIRef(QUINCE_DEFAULT_GRAPH_IRI)

    def __str__(self):
        return 'default'

    def get_context(self, c, **kwargs):
        self.current_context = c

    def add(self, triple):
        self.sink.quad(triple[0], triple[1]. triple[2], self.current_context)


class QuinceStore:

    IRI_MATCH = r'\<[^\>]*\>'
    LITERAL_MATCH = r'"[^"\\]*(?:\\.[^"\\]*)*"(\^\^\<[^\>]*\>)?(@[^\s]*)?'
    URI_OR_LITERAL_MATCH = IRI_MATCH + r'|' + LITERAL_MATCH

    def __init__(self, path, default_graph=None):
        self.root = os.path.abspath(path)
        self.default_graph = default_graph or QUINCE_DEFAULT_GRAPH_IRI

    def assert_quad(self, s, p, o, g=None):
        s, p, o = self.skolemize(s, p, o)
        subject_file_path = self.make_file_path(s) + NQOUT
        object_file_path = self.make_file_path(o) + NQIN
        nq = self.make_nquad(s, p, o, g or self.default_graph)
        self.assert_quad_in_file(subject_file_path, nq)
        self.assert_quad_in_file(object_file_path, nq)

    def retract_quad(self, s, p, o, g=None):
        subject_file_path = self.make_file_path(s) + NQOUT
        object_file_path = self.make_file_path(o) + NQIN
        nq = self.make_nquad_pattern(s, p, o, g or self.default_graph)
        self.retract_quads_from_file(subject_file_path, nq)
        self.retract_quads_from_file(object_file_path, nq)

    def exists(self, s, p, o, g=None):
        subject_file_path = self.make_file_path(s) + NQOUT
        nq = self.make_nquad_pattern(s, p, o, g or self.default_graph)
        return self.match_quads_in_file(subject_file_path, nq)

    def skolemize(self, s, p, o):
        if isinstance(s, rdflib.BNode):
            s = s.skolemize()
        if isinstance(p, rdflib.BNode):
            p = p.skolemize()
        if isinstance(o, rdflib.BNode):
            o = o.skolemize()
        return s, p, o

    def flush(self):
        pass

    def make_file_path(self, node):
        h = hashlib.sha1(node.n3().encode()).hexdigest()
        return os.path.join(self.root, h[:2], h[2:])

    def make_nquad(self, s, p, o, g):
        return "{0} {1} {2} {3} .\n".format(s.n3(), p.n3(), o.n3(), g.n3())

    def make_nquad_pattern(self, s, p, o, g):
        return "{0} {1} {2} {3} .\n".format(
            QuinceStore.IRI_MATCH if '*' == s else re.escape(s.n3()),
            QuinceStore.IRI_MATCH if '*' == p else re.escape(p.n3()),
            QuinceStore.URI_OR_LITERAL_MATCH if '*' == o else re.escape(o.n3()),
            QuinceStore.IRI_MATCH if '*' == g else re.escape(g.n3())
        )

    def assert_quad_in_file(self, file_path, nquad):
        lines = self.load(file_path)
        ins = bisect.bisect(lines, nquad)
        if ins == 0 or lines[ins] != nquad:
            lines.insert(ins, nquad)
        # TODO - cache file contents and write them all on flush
        self.flush_file(file_path, lines)

    def retract_quads_from_file(self, file_path, pattern):
        lines = self.load(file_path)
        lines = list(filter(lambda x: not(re.fullmatch(pattern, x)), lines))
        self.flush_file(file_path, lines)

    def match_quads_in_file(self, file_path, pattern):
        lines = self.load(file_path)
        return filter(lambda x: not(re.fullmatch(pattern, x)), lines)

    def load(self, p):
        if not os.path.exists(p):
            return []
        with open(p, encoding='utf-8', mode='r') as f:
            return f.readlines()

    def flush_file(self, p, lines):
        if not os.path.exists(os.path.dirname(p)):
            os.mkdir(os.path.dirname(p))
        with open(p, encoding='utf-8', mode='w') as f:
            f.writelines(lines)


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = collections.OrderedDict()

    def get(self, key, default=None):
        try:
            value = self.capacity.pop(key)
            self.cache[key] = value
        except KeyError:
            return default

    def set(self, key, value):
        try:
            self.cache.pop(key)
        except KeyError:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
        self.cache[key] = value