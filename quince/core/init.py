__author__ = 'Kal Ahmed'

import logging
import os

from quince.core import repo as repo_lib

# Return codes
SUCCESS = 1
NOTHING_TO_INIT = 2

# Hooks to add
QUINCE_HOOKS = {
    'post-merge': '''
# Quince post-merge clean-up
echo Calling quince post-merge clean-up
if quince sort -s "HEAD^"
then
    echo Post-merge clean-up completed OK
    exit 0
else
    echo Error running post-merge clean-up
    echo You may need to run the quince sort command manually to return the repository to a consistent state
    exit 1
fi'''
}


def init_cwd():
    """Makes the current working directory a Quince repository"""
    log = logging.getLogger('quince')
    if repo_lib.git_dir():
        if os.path.exists(repo_lib.qdir()):
            log.warn('Nothing to init. There is already a quince repository at {0}'.format(repo_lib.qdir()))
            return NOTHING_TO_INIT
        else:
            repo_lib.init(repo_lib.git_dir())
            log.info('Quince repository added to existing git repository at {0}'.format(repo_lib.qdir()))
    else:
        repo_lib.init(os.getcwd(), init_git=True)
        log.info('New quince repository created at {0}'.format(os.getcwd()))
    add_hooks()
    return SUCCESS


def add_hooks():
    """
    Sets up the default git hooks for quince
    :return:
    """
    hooks_path = os.path.join(repo_lib.git_dir(), 'hooks')
    if not os.path.exists(hooks_path):
        os.makedirs(hooks_path)
    for hook in QUINCE_HOOKS:
        hook_script_path = os.path.join(hooks_path, hook)
        if not os.path.exists(hook_script_path):
            with open(hook_script_path, 'w') as f:
                f.write('#!/bin/sh\n')
                f.write(QUINCE_HOOKS[hook])
        else:
            with open(hook_script_path, 'a') as f:
                f.write('\n')
                f.write(QUINCE_HOOKS[hook])
        # Ensure the file is executable
        os.chmod(hook_script_path, 0o777)
