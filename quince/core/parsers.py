__author__ = 'Kal Ahmed'

from codecs import getreader

from rdflib.plugins.parsers.ntriples import NTriplesParser
from rdflib.plugins.parsers.ntriples import ParseError
from rdflib.plugins.parsers.ntriples import r_tail
from rdflib.plugins.parsers.ntriples import r_wspace
from rdflib.util import guess_format


def get_parser(file_path, sink):
    fmt = guess_format(file_path)
    if fmt == 'nt':
        return NTriplesParser(sink=sink)
    if fmt == 'nquads':
        return NQuadsParser(sink)
    return None


class NQuadsParser(NTriplesParser):

    def __init__(self, sink):
        super().__init__()
        self.sink = sink
        self.file = None
        self.buffer = None
        self.line = None

    def parse(self, source):
        """Parse f as an N-Triples file."""

        if not hasattr(source, 'read'):
            raise ParseError("Item to parse must be a file-like object.")

        source = getreader('utf-8')(source)

        self.file = source
        self.buffer = ''
        while True:
            self.line = __line = self.readline()
            if self.line is None:
                break
            try:
                self.parseline()
            except ParseError as msg:
                raise ParseError("Invalid line (%s):\n%r" % (msg, __line))

        return self.sink

    def parseline(self):
        self.eat(r_wspace)
        if (not self.line) or self.line.startswith('#'):
            return  # The line is empty or a comment

        subject = self.subject()
        self.eat(r_wspace)

        predicate = self.predicate()
        self.eat(r_wspace)

        obj = self.object()
        self.eat(r_wspace)

        context = self.uriref() or self.nodeid()
        self.eat(r_tail)

        if self.line:
            raise ParseError("Trailing garbage")
        # Must have a context aware store - add on a normal Graph
        # discards anything where the ctx != graph.identifier
        self.sink.quad(subject, predicate, obj, context)