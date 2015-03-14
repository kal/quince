__author__ = 'Kal Ahmed'

import re
from quince.core.repo import QuinceStore
from quince.core.exceptions import QuinceNoSerializerException

class Serializer:
    LINE_REGEX = re.compile(r"(?P<s>" + QuinceStore.IRI_MATCH + r")\s+(?P<p>" + QuinceStore.IRI_MATCH + r")\s+" +
                            r"(?P<o>" + QuinceStore.URI_OR_LITERAL_MATCH + ")\s+" +
                            r"(?P<g>" + QuinceStore.IRI_MATCH + ")\s*\.\s*\n")

    def __init__(self, stream, encoding=None):
        self.stream = stream
        self.encoding = encoding

    def on_start(self):
        pass

    def on_line(self, line):
        # TODO parse the line (using rdflib?) and then call on_quad with the separate elements
        pass

    def on_quad(self, s, p, o, g):
        pass

    def on_end(self):
        pass


class NTriplesSerializer(Serializer):
    """
    Serializes quads to NTriples format.
    NOTE: this serializer simply drops the graph from the quad - effectively merging all graphs
    """
    def on_line(self, line):
        m = Serializer.LINE_REGEX.fullmatch(line)
        if m:
            l = "{0} {1} {2} .\n".format(m.group('s'),
                                         m.group('p'),
                                         m.group('o'))
            self.stream.write(l.encode(self.encoding, "replace"))


class NQuadsSerializer(Serializer):
    """
    Serializes quads to NQuads format.
    This is essentially a pass-thru serializer. The only task it performs is encoding the line
    to the output encoding of the stream.
    """
    def on_line(self, line):
        self.stream.write(line.encode(self.encoding, "replace"))

serializers = {"nt": NTriplesSerializer,
               "nquads": NQuadsSerializer}

supported_formats = list(serializers.keys())


def get_serializer(fmt, stream, encoding):
    if fmt not in serializers:
        raise QuinceNoSerializerException(fmt)
    return serializers[fmt](stream, encoding)

