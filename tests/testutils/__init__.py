__author__ = 'Kal Ahmed'

import os
import shutil


def ensure_empty_dir(path):
    p = os.path.join('tmp', path)
    if os.path.isdir(p):
        shutil.rmtree(p)
    os.makedirs(p)
    return p


def get_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()


def make_nquad(s, p, o, g):
    return "{0} {1} {2} {3} .\n".format(s.n3(), p.n3(), o.n3(), g.n3())

