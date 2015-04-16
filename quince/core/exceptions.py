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


class QuinceNamespaceExistsException(QuinceException):
    """Raised when an attempt is made to overwrite an existing namespace definition
        in the local quince configuration file."""
    pass


class QuinceNoSuchNamespaceException(QuinceException):
    """Raised when an attempt is made to retrieve the expansion value for an undefined namespace prefix"""


class QuinceRemoteExistsException(QuinceException):
    def __init__(self, remote_name):
        self.remote_name = remote_name
        self.message = 'A remote with the name "' + remote_name + '" already exists.'

class QuinceNoSuchRemoteException(QuinceException):
    def __init__(self, remote_name):
        self.remote_name = remote_name
        self.message = 'No remote with the name "' + remote_name + '".'

class QuinceArgumentException(QuinceException):
    def __init__(self, msg):
        self.message = msg


class QuinceMultiException(QuinceException):
    def __init__(self, inner_exceptions):
        self.message = 'Multiple errors were raised.'
        self.inner_exceptions = inner_exceptions