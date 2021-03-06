#!/usr/bin/env python
__author__ = 'Kal Ahmed'

import sys

from setuptools import setup


reqs = ['GitPython==1.0.1', 'clint==0.4.1', 'rdflib==4.2.0', 'rfc3987==1.3.4']
if (3, 3) > sys.version_info > (3, 0):
    reqs.append('argparse')

long_desc = """
Quince is a version control system for RDF data built on top of Git.
"""

setup(
    name='quince',
    version='0.1.0',
    description='A version control system for RDF',
    author='Kal Ahmed',
    author_email='kal@networkedplanet.com',
    packages=['quince', 'quince.core', 'quince.cli'],
    install_requires=reqs,
    license='GPLv3',
    classifiers=(),
    entry_points={
        'console_scripts': [
            'quince = quince.cli.quince:main'
        ]},
)