__author__ = 'Kal Ahmed'

import os
import cProfile
import time
from quince.cli import quince

if __name__ == "__main__":
    if os.environ.get('PROFILE', None):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = quince.main()
            profile.disable()
        finally:
            profile.print_stats()
    else:
        start = time.clock()
        quince.main()
        end = time.clock()
        print('Command execution took {:3f} seconds'.format(end-start))