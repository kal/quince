__author__ = 'Kal Ahmed'

from quince.core.repo import QuinceStore, qdir


def add(prefix, iri):
    store = QuinceStore(qdir())
    store.add_namespace(prefix, iri)


def remove(prefix):
    store = QuinceStore(qdir())
    store.remove_namespace(prefix)


def get_mappings():
    store = QuinceStore(qdir())
    return store.ns_prefix_mappings