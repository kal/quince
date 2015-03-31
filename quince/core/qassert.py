__author__ = 'Kal Ahmed'

import re

import rfc3987
from rdflib import URIRef, Literal

from quince.core.repo import QuinceStore, qdir, git_add_files
from quince.core.exceptions import QuinceArgumentException, QuinceMultiException

CURIE = re.compile(r'\[(?P<prefix>[^:]+):(?P<ref>[^\]]+)\]')
LITERAL = re.compile(r'"(?P<lit>[^"\\]*(?:\\.[^"\\]*)*)"(\^\^<(?P<dt>[^>]*)>)?(@(?P<lang>[^\s]*))?')


def assert_quad(subj, pred, obj, graph):
    store = QuinceStore(qdir())
    s, p, o, g = make_quad(store, subj, pred, obj, graph)
    store.assert_quad(s, p, o, g)
    store.flush()
    git_add_files()
    return s, p, o, g


def retract_quad(subj, pred, obj, graph):
    store = QuinceStore(qdir())
    s, p, o, g = make_quad(store, subj, pred, obj, graph, True)
    retracted = store.retract_quad(s, p, o, g)
    store.flush()
    git_add_files()
    # TODO: This should really return a list containing all of the quads that were matched and retracted
    return retracted


def make_quad(store, subj, pred, obj, graph, allow_wildcards=False):
    prefix_mappings = store.ns_prefix_mappings
    errors = []
    s = p = o = g = None
    try:
        if allow_wildcards and subj == '*':
            s = '*'
        else:
            s = make_node(subj, prefix_mappings)
    except QuinceArgumentException as e:
        errors.append(e)
    try:
        if allow_wildcards and pred == '*':
            p = '*'
        else:
            p = make_node(pred, prefix_mappings)
    except QuinceArgumentException as e:
        errors.append(e)
    try:
        if allow_wildcards and obj == '*':
            o = '*'
        else:
            o = make_node(obj, prefix_mappings, True)
    except QuinceArgumentException as e:
        errors.append(e)
    try:
        if allow_wildcards and graph == '*':
            g = '*'
        else:
            g = make_node(graph, prefix_mappings)
    except QuinceArgumentException as e:
        errors.append(e)
    if len(errors) > 0:
        raise QuinceMultiException(errors)
    return s, p, o, g


def make_node(v, prefix_mappings, allow_literals=False):
    if allow_literals:
        n = parse_literal(v)
        if n is not None:
            return n
    n = expand_iri(v, prefix_mappings)
    if n is None:
        if allow_literals:
            raise QuinceArgumentException('Could not parse "{0}" as a literal, safe CURIE or absolute IRI.'.format(v))
        else:
            raise QuinceArgumentException('Could not parse "{0}" as a safe CURIE or absolute IRI.'.format(v))
    return n


def expand_iri(s, prefix_mappings):
    m = CURIE.match(s)
    if m:
        if m.group('prefix') in prefix_mappings:
            s = prefix_mappings[m.group('prefix')] + m.group('ref')
    m = rfc3987.match(s, 'absolute_IRI')
    return URIRef(s) if m else None


def parse_literal(l):
    m = LITERAL.match(l)
    if m:
        return Literal(m.group('lit'), datatype=m.group('dt'), lang=m.group('lang'))
    return None