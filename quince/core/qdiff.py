__author__ = 'Kal Ahmed'

from itertools import dropwhile
import re

import git

from quince.core.repo import git_dir, QUINCE_DIR, QuinceStore

LINE_REGEX = re.compile(r"(?P<s>" + QuinceStore.IRI_MATCH + r")\s+(?P<p>" + QuinceStore.IRI_MATCH + r")\s+" +
                        r"(?P<o>" + QuinceStore.URI_OR_LITERAL_MATCH + ")\s+" +
                        r"(?P<g>" + QuinceStore.IRI_MATCH + ")\s*\.\s*")

def generate_diffs(commits=None, resource=None, graph=None, output_format='nquad_diff'):
    g = git.Repo(git_dir())
    commits = commits or []
    diff_list = SparqlDiffList() if output_format == 'sparql' else DiffList()
    if len(commits) == 0:
        head_commit = g.head.commit
        diff_index = head_commit.diff(paths=QUINCE_DIR, create_patch=True)
    elif len(commits) == 1:
        to_commit = g.commit(commits[0])
        diff_index = to_commit.diff(paths=QUINCE_DIR, create_patch=True)
    else:
        from_commit = g.commit(commits[0])
        to_commit = g.commit(commits[1])
        diff_index = from_commit.diff(to_commit, paths=QUINCE_DIR, create_patch=True)
    for diff in diff_index:
        diff_str = diff.diff.decode()
        for line in filter(lambda x: _filter_diff(x, resource, graph),  dropwhile(lambda x: not(x.startswith("@@")), diff_str.split("\n"))):
            diff_list.add(line.strip())
    return diff_list


def _filter_diff(diff, resource, graph):
    if not(diff.startswith('+') or diff.startswith('-')):
        return False
    if not resource or graph:
        return True
    matches = LINE_REGEX.match(diff, 1)
    if not matches:
        return False
    if resource and matches.group('s') != resource:
        return False
    if graph and matches.group('g') != graph:
        return False
    return True


class SparqlDiffList:
    def __init__(self):
        self.graphs = {}

    def add(self, diff_quad):
        matches = LINE_REGEX.match(diff_quad, 1)
        if matches:
            graph = matches.group('g')
            if graph:
                if graph not in self.graphs:
                    self.graphs[graph] = DiffList()
                diff_triple = '{0}{1} {2} {3} .'.format(
                    diff_quad[0],
                    matches.group('s'),
                    matches.group('p'),
                    matches.group('o')
                )
                self.graphs[graph].add(diff_triple)

    def to_string(self):
        deletions = ''
        insertions = ''
        for g in self.graphs:
            diff_list = self.graphs[g]
            if len(diff_list.deletions) > 0:
                deletions += 'GRAPH {0} {{\n'.format(g)
                deletions += '\n'.join(diff_list.deletions)
                deletions += '\n}'
            if len(diff_list.insertions) > 0:
                insertions += 'GRAPH {0} {{\n'.format(g)
                insertions += '\n'.join(diff_list.insertions)
                insertions += '\n}'
        ret = ''
        if len(deletions) > 0:
            ret = '\n'.join(['DELETE DATA {', deletions, '}'])
        if len(insertions) > 0:
            ret += '\n'.join(['INSERT DATA {', insertions, '}'])
        return ret

    def __len__(self):
        return sum(map(lambda x: len(x), self.graphs.values()))

    def any(self):
        return any(filter(lambda x: x.any(), self.graphs.values()))



class DiffList:
    def __init__(self):
        self.insertions = []
        self.deletions = []

    def add(self, diff_quad):
        if diff_quad.startswith('+'):
            self.insertions.append(diff_quad[1:])
        elif diff_quad.startswith('-'):
            self.deletions.append(diff_quad[1:])

    def to_string(self):
        return '\n'.join(self.deletions) + '\n||\n' + '\n'.join(self.insertions)

    def __len__(self):
        return len(self.insertions) + len(self.deletions)

    def any(self):
        return len(self) > 0
