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
        self.update_manager = CachingFileManager(10000)

    def assert_quad(self, s, p, o, g=None):
        s, p, o = self.skolemize(s, p, o)
        subject_file_path = self.make_file_path(s) + NQOUT
        object_file_path = self.make_file_path(o) + NQIN
        nq = self.make_nquad(s, p, o, g or self.default_graph)
        self.update_manager.add_line_to_file(subject_file_path, nq)
        self.update_manager.add_line_to_file(object_file_path, nq)

    def retract_quad(self, s, p, o, g=None):
        subject_file_path = self.make_file_path(s) + NQOUT
        object_file_path = self.make_file_path(o) + NQIN
        nq = self.make_nquad_pattern(s, p, o, g or self.default_graph)
        self.update_manager.remove_line_from_file(subject_file_path, nq)
        self.update_manager.remove_line_from_file(object_file_path, nq)

    def exists(self, s, p, o, g=None):
        subject_file_path = self.make_file_path(s) + NQOUT
        nq = self.make_nquad_pattern(s, p, o, g or self.default_graph)
        return self.match_quads_in_file(subject_file_path, nq)

    def flush(self):
        self.update_manager.flush()

    def make_file_path(self, node):
        """
        Generates the path to the file that contains the quads for a given node. This is the method by which
        quince splits the RDF graphs across multiple NQuad files. If a single NQuad file contains more distinct
        nodes, performance improves due to fewer file accesses at the cost of larger files that need to be processed
        (and cached).

        :param node: The RDFLib Resource to be mapped to a file path
        :return: A file path
        """
        h = hashlib.sha1(node.n3().encode()).hexdigest()
        # This option will create a separate file for each distinct hash. The files are grouped into directories
        # using the most significant byte of the hash
        return os.path.join(self.root, h[:2], h)

        # This option will create 2 levels of directory, using the first and then the second most significant byte
        # It keeps each distinct hash in a separate file.
        # return os.path.join(self.root, h[:2], h[:4], h)

        # This option will create files that contain a merge of several hashes
        # return os.path.join(self.root, h[:3])

    def match_quads_in_file(self, file_path, pattern):
        lines = self.update_manager.iter_lines(file_path)
        return filter(lambda x: re.fullmatch(pattern, x), lines)

    @staticmethod
    def make_nquad(s, p, o, g):
        return "{0} {1} {2} {3} .\n".format(s.n3(), p.n3(), o.n3(), g.n3())

    @staticmethod
    def make_nquad_pattern(s, p, o, g):
        return "{0} {1} {2} {3} .\n".format(
            QuinceStore.IRI_MATCH if '*' == s else re.escape(s.n3()),
            QuinceStore.IRI_MATCH if '*' == p else re.escape(p.n3()),
            QuinceStore.URI_OR_LITERAL_MATCH if '*' == o else re.escape(o.n3()),
            QuinceStore.IRI_MATCH if '*' == g else re.escape(g.n3())
        )

    @staticmethod
    def skolemize(s, p, o):
        if isinstance(s, rdflib.BNode):
            s = s.skolemize()
        if isinstance(p, rdflib.BNode):
            p = p.skolemize()
        if isinstance(o, rdflib.BNode):
            o = o.skolemize()
        return s, p, o


class SortedSet:
    def __init__(self, iterable=None):
        self.list = list(iterable) if iterable else []
        self.list.sort()

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return iter(self.list)

    def __contains__(self, item):
        i = bisect.bisect_left(self.list, item)
        j = bisect.bisect_right(self.list, item)
        return i != j

    def insert(self, v):
        ins = bisect.bisect(self.list, v)
        if ins == len(self.list) and (ins == 0 or self.list[ins-1] != v):
            # Insert location is at the end of the list.
            # Only insert if the current last element != v
            self.list.append(v)
        elif (ins == 0) or (self.list[ins-1] != v):
            # Insert location is at the start of the list
            # Must be OK to insert
            self.list.insert(ins, v)

    def index(self, item):
        i = bisect.bisect_left(self.list, item)
        j = bisect.bisect_right(self.list, item)
        return self.list[i:j].index(item) + i

    def remove(self, item):
        i = self.index(item)
        del self.list[i]


class FileEntry(SortedSet):
    def __init__(self, file_path):
        self.path = file_path
        if os.path.exists(file_path):
            with open(file_path, encoding='utf-8', mode='r') as f:
                SortedSet.__init__(self, f.readlines())
        else:
            SortedSet.__init__(self, None)

    def flush(self):
        self._ensure_directory(os.path.dirname(self.path))
        with open(self.path, encoding='utf-8', mode='w') as f:
            f.writelines(self.list)

    @staticmethod
    def _ensure_directory(dir_name):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)


class CachingFileManager:
    def __init__(self, cache_capacity):
        """
        The CachingFileManager provides a basic interface for reading and modifying text file content
        while using an LRU cache to minimize disk access. Operations on files are line-based and
        use the :class:`FileEntry` interface. File updates are persisted to disk only when the
         flush() method is called or when a file entry is evicted from the cache.
        :param cache_capacity: The maximum number of cached file entries
        """
        self.cache = LRUCache(cache_capacity, eviction_callback=lambda x, y: y.flush())

    def add_line_to_file(self, file_path, line):
        """
        Inserts the specified line into the file at the specified file path,
        maintaining the sort order of lines in the file.

        Updates are applied only to the cached file representation. The file on disk is not updated until either
        the flush method is called or the file entry is evicted from the cache.

        :param file_path: The path to the file to be updated
        :param line: The line to be inserted into the file
        :return: None
        """
        file = self._assert_file(file_path)
        file.insert(line)

    def remove_line_from_file(self, file_path, line):
        """
        Removes the line matching `line` from the specified file.
        If the file does not exist or does not contain the line, this method is a no-op.

        Updates are applied only to the cached file representation. The file on disk
        is not updated until either the flush method is called or the file entry is
        evicted due to the file cache capacity being reached.

        :param file_path: The path to the file to be updated
        :param line: The line to be removed from the file
        :return: None
        """
        file = self._assert_file(file_path)
        file.remove(line)

    def iter_lines(self, file_path):
        """
        Returns an iterator over the lines in the file at file_path
        :param file_path: The path to the file to be read
        :return: An iterator over the lines in the specified file. If
        the file does not exist, an empty iterator is returned.
        """
        file = self._assert_file(file_path)
        return iter(file)

    def _assert_file(self, file_path):
        file = self.cache.get(file_path)
        if file is None:
            file = FileEntry(file_path)
            self.cache.set(file_path, file)
        return file

    def flush(self):
        """
        Writes pending changes to disk.
        :return: None
        """
        for f in self.cache.items():
            f.flush()


class LRUCache:
    def __init__(self, capacity, eviction_callback=None):
        self.capacity = capacity
        self.cache = collections.OrderedDict()
        self.eviction_callback = eviction_callback

    def __contains__(self, key):
        return key in self.cache

    def get(self, key, default=None):
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except KeyError:
            return default

    def set(self, key, value):
        try:
            self.cache.pop(key)
        except KeyError:
            if len(self.cache) >= self.capacity:
                key, evicted = self.cache.popitem(last=False)
                if self.eviction_callback:
                    self.eviction_callback(key, evicted)
        self.cache[key] = value

    def drop(self, key):
        try:
            self.cache.pop(key)
        except KeyError:
            # Swallow the error
            pass

    def items(self):
        return self.cache.values()
