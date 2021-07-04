''' Tests for the documentation examples
'''
import c3d
import io
import unittest
import numpy as np
from test.base import Base

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..\\examples'))


class Examples(Base):
    ''' Test basic writer functionality
    '''
    def test_write(self):
        import write
        # Raises 'FileNotFound' if the file was not generated
        os.remove('..\\random-points.c3d')


if __name__ == '__main__':
    unittest.main()
