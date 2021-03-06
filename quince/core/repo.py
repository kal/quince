__author__ = 'Kal Ahmed'

import bisect
import collections
import configparser
from enum import Enum
import glob
import hashlib
import itertools
import logging
import os
import re

import git
import git.cmd
import rdflib

from quince.core.exceptions import QuincePreconditionFailedException, QuinceNamespaceExistsException, \
    QuinceNoSuchNamespaceException, QuinceRemoteExistsException, QuinceNoSuchRemoteException

QUINCE_DIR = '.quince'
QUINCE_DEFAULT_GRAPH_IRI = 'http://networkedplanet.com/quince/.well-known/default-graph'
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
    g = git_dir()
    return g[:-4] if g is not None else None


def qdir():
    """Get the full path to the .quince directory of the Git repo."""
    return os.path.join(repo_dir(), QUINCE_DIR)


def init(path, init_git=False):
    if init_git:
        git.Repo.init(path)
    old_wd = os.path.abspath(os.getcwd())
    try:
        os.chdir(path)
        dir_path = qdir()
        os.mkdir(dir_path)
        config_path = os.path.join(dir_path, 'config')
        open(config_path, 'w').close()
    finally:
        os.chdir(old_wd)


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
    URI_OR_LITERAL_MATCH = '(' + IRI_MATCH + '|' + LITERAL_MATCH + ')'

    def __init__(self, path, default_graph=None):
        self.root = os.path.abspath(path)
        self.default_graph = default_graph or rdflib.URIRef(QUINCE_DEFAULT_GRAPH_IRI)
        self.update_manager = CachingFileManager(10000)
        self._config = None

    @property
    def config(self):
        if self._config is None:
            self._config = configparser.ConfigParser()
            self._config.read([os.path.join(self.root, 'config'), os.path.expanduser('~/.quinceconfig')])
        return self._config

    def add_namespace(self, prefix, iri):
        config = self.config
        try:
            ns_section = config['Namespaces']
        except KeyError:
            config.add_section('Namespaces')
            ns_section = config['Namespaces']
        if prefix in ns_section:
            raise QuinceNamespaceExistsException()
        ns_section[prefix] = iri
        self._flush_config()

    def remove_namespace(self, prefix):
        config = self.config
        try:
            ns_section = config['Namespaces']
        except KeyError:
            # No namespaces section so nothing to remove
            return
        if prefix in ns_section:
            del ns_section[prefix]
            self._flush_config()

    def add_remote(self, name, endpoint):
        """
        Add a configuration entry for a new remote

        :param name: The remote name
        :param endpoint: The remote endpoint IRI
        :raises: QuinceRemoteExistsException if a remote with the specified name already exists
        """
        config = self.config
        section_name = 'Remote "{0}"'.format(name)
        if section_name in config:
            raise QuinceRemoteExistsException(name)
        else:
            config.add_section(section_name)
            section = config[section_name]
            section['endpoint'] = endpoint
        self._flush_config()

    def remove_remote(self, name):
        """
        Remove a configuration entry for a remote

        :param name:
        :raises: QuinceNoSuchRemoteException if a remote with the specified name does not exist
        """
        config = self.config
        section_name = 'Remote "{0}"'.format(name)
        try:
            section = config[section_name]
        except:
            raise QuinceNoSuchRemoteException(name)
        config.remove_section(section_name)
        remote_file_path = os.path.join(self.root, 'remotes', name)
        if os.path.exists(remote_file_path):
            os.remove(remote_file_path)

    @property
    def ns_prefix_mappings(self):
        try:
            return self.config['Namespaces']
        except KeyError:
            return {}

    def expand_ns_prefix(self, prefix):
        if prefix in self.config['Namespaces']:
            return self.config['Namespaces'][prefix]
        raise QuinceNoSuchNamespaceException()

    def _flush_config(self):
        with open(os.path.join(self.root, 'config'), 'w') as f:
            self.config.write(f)

    def assert_quad(self, s, p, o, g=None):
        s, p, o = self.skolemize(s, p, o)
        subject_file_path = self.make_file_path(s) + NQOUT
        nq = self.make_nquad(s, p, o, g or self.default_graph)
        self.update_manager.add_line_to_file(subject_file_path, nq)

    def retract_quad(self, s, p, o, g=None):
        subject_file_path = self.make_file_path(s) + NQOUT
        nq = self.make_nquad_pattern(s, p, o, g or self.default_graph)
        print(nq)
        return self.update_manager.remove_lines_from_file(subject_file_path, nq)

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

    def sort_quads(self, path_iter=None):
        """
        Ensure that the contents of the nquads files are in sorted order.
        :param path_iter: An iterable that yields the paths to each file to be sorted. If not specified
            an iterator over all of the files in the store will be used.
        """
        log = logging.getLogger('quince')
        path_iter = path_iter or self._iterate_quad_files()
        visit_count = 0
        for file_path in path_iter:
            log.debug(file_path)
            self.update_manager.touch(file_path)
            visit_count += 1
        log.debug('{0} files visited. Writing updates to disk - this may take a while...'.format(visit_count))
        self.update_manager.flush()

    def _iterate_quad_files(self):
        """
        Return an iterator over the nquads files in the repository
        """
        return glob.iglob(os.path.join(self.root, '*', '*.nqo'))

    def all_quads(self, graphs):
        filter_regex = None if graphs is None else "|".join(map(lambda x: "(" + re.escape(x) + ")", graphs)) + r"\s*.\s*\n$"
        for root, dirs, files in os.walk(self.root):
            for f in filter(lambda x: x.endswith(NQOUT), files):
                for l in self.update_manager.iter_lines(os.path.join(root, f)):
                    if filter_regex is None or re.search(filter_regex, l):
                        yield l

    def match_quads_in_file(self, file_path, pattern):
        lines = self.update_manager.iter_lines(file_path)
        return filter(lambda x: re.match(pattern, x), lines)

    @staticmethod
    def make_nquad(s, p, o, g):
        if isinstance(o, rdflib.Literal):
            return "{0} {1} {2} {3} .\n".format(s.n3(), p.n3(), _xmlcharref_encode(_quote_literal(o)), g.n3())
        else:
            return "{0} {1} {2} {3} .\n".format(s.n3(), p.n3(), o.n3(), g.n3())

    @staticmethod
    def make_nquad_pattern(s, p, o, g):
        return r"{0}\s+{1}\s+{2}\s+{3}\s+.".format(
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


def _quote_literal(l):
    """
    Handles proper NQuads escaping of an rdflib Literal.
    """
    encoded = _quote_encode(l)
    if l.language:
        if l.datatype:
            raise Exception("Literal has datatype AND language!")
        return '%s@%s' % (encoded, l.language)
    elif l.datatype:
        return '%s^^<%s>' % (encoded, l.datatype)
    else:
        return '%s' % encoded


def _quote_encode(l):
    return '"%s"' % l.replace('\\', '\\\\')\
        .replace('\n', '\\n')\
        .replace('"', '\\"')\
        .replace('\r', '\\r')


# from <http://code.activestate.com/recipes/303668/>
def _xmlcharref_encode(unicode_data, encoding="ascii"):
    """Emulate Python 2.3's 'xmlcharrefreplace' encoding error handler."""
    res = ""

    # Step through the unicode_data string one character at a time in
    # order to catch unencodable characters:
    for char in unicode_data:
        try:
            char.encode(encoding, 'strict')
        except UnicodeError:
            if ord(char) <= 0xFFFF:
                res += '\\u%04X' % ord(char)
            else:
                res += '\\U%08X' % ord(char)
        else:
            res += char
    return res


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

    def remove_matches(self, pattern):
        to_delete = []
        deleted = []
        for index, item in enumerate(self.list):
            print(item)
            if pattern.match(item, ):
                print('MATCH')
                to_delete.append(index)
        to_delete.reverse()
        for index in to_delete:
            deleted.append(self.list[index])
            del self.list[index]
        return deleted


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

    def remove_lines_from_file(self, file_path, pattern):
        file = self._assert_file(file_path)
        compiled_pattern = re.compile(pattern)
        return file.remove_matches(compiled_pattern)

    def iter_lines(self, file_path):
        """
        Returns an iterator over the lines in the file at file_path
        :param file_path: The path to the file to be read
        :return: An iterator over the lines in the specified file. If
        the file does not exist, an empty iterator is returned.
        """
        file = self._assert_file(file_path)
        return iter(file)

    def touch(self, file_path):
        """
        loads the file at the specified file path.
        :param file_path:
        :return:
        """
        self._assert_file(file_path)

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


def git_add_files():
    """git-add .quince directory and all of its contents"""
    q = os.path.relpath(qdir())
    g = git.cmd.Git()
    g.init()
    g.add(q)
