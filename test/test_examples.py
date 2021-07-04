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
    def test_read(self):
        import read

    def test_write(self):
        import write
        path = 'random-points.c3d'

        with open(path, 'rb') as f:
            reader = c3d.Reader(f)
            assert reader.frame_count == 100, \
                'Expected 30 point frames in write.py test, was {}'.format(reader.frame_count)
            assert reader.point_used == 24, \
                'Expected 5 point samples in write.py test, was {}'.format(reader.point_used)
        # Raises 'FileNotFound' if the file was not generated
        os.remove(path)

    def test_edit(self):
        import edit
        path = 'my-looped-motion.c3d'

        with open(path, 'rb') as f:
            reader = c3d.Reader(f)
            assert reader.frame_count == 900, \
                'Expected 900 point frames in edit.py test, was {}'.format(reader.frame_count)
        # Raises 'FileNotFound' if the file was not generated
        os.remove(path)

if __name__ == '__main__':
    unittest.main()
