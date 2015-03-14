__author__ = 'Kal Ahmed'


class QuinceException(Exception):
    pass


class QuinceParseException(QuinceException):
    def __init__(self, source, parser_msg):
        self.source = source
        self.parser_msg = parser_msg
        self.message = "Error parsing '{0}'. Parser reports: {1}".format(source, parser_msg)


class QuinceNoParserException(QuinceException):
    def __init__(self, source):
        self.source = source
        self.message = "No parser available for the file {0}".format(source)


class QuinceNoSerializerException(QuinceException):
    def __init__(self, fmt):
        self.format = fmt
        self.message = "No serializer available for the format '{0}'".format(fmt)


class QuincePreconditionFailedException(QuinceException):
    """Raised when an expected triple does not exist in the store, or an unexpected
    triple does exist in the store."""
    def __init__(self, mode, s, p, o, g):
        self.mode = mode
        self.subj = s
        self.pred = p
        self.obj = o
        self.graph = g
        self.message = "Precondition failed: {0} for {1} {2} {3} {4}".format(mode, s, p, o, g)