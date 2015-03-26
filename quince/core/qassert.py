__author__ = 'Kal Ahmed'

from rdflib import URIRef
from quince.core.repo import QuinceStore, qdir, git_add_files


def assert_quad(subj, pred, obj, graph):
    store = QuinceStore(qdir())
    s = make_node(subj)
    p = make_node(pred)
    o = make_node(obj, True)
    g = make_node(graph)
    store.assert_quad(s, p, o, g)
    store.flush()
    git_add_files()


def make_node(v, allow_literals=False):
    # TODO: distinguish between URI, CURIE and literal
    # For now we are assuming we only get IRIs
    return URIRef(v)