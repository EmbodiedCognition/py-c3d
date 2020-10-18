import c3d
import importlib
import io
import os
import unittest
import numpy as np
from test.base import Base
from test.zipload import Zipload

class FrameCountEncodingTest():
    ''' Base class testing if frame count can be read when encoded differently.
    '''

    def test_a_read(self):

        print('----------------------------')
        print(type(self))
        print('----------------------------')

        for file in files:
            reader = c3d.Reader(Zipload._get(self.ZIP, file))
            self._log(reader)

            # Verify file count

        print('{} | READ: OK'.format(folder))



class Sample36(FrameCountEncodingTest, Base):
    ZIP = 'sample00.zip'

    count = '18124', '36220', '72,610'
    zip_files = []

class Sample31(FrameCountEncodingTest, Base):
    ZIP = 'sample00.zip'

    count = ''
    zip_files = []

if __name__ == '__main__':
    unittest.main()
