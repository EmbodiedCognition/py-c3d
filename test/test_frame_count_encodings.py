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

        for file, frame_count in zip(self.zip_files, self.frame_count):
            reader = c3d.Reader(Zipload._get(self.ZIP, file))
            self._log(reader)

            # Verify file count

            assert reader.frame_count == frame_count,\
                   'Wrong frame count read from file {}/{}. Expected {} was {}'.format(
                   self.ZIP, file, frame_count, reader.frame_count)

            point, analog = Base.load_data(reader)
            print('{} | FRAME_COUNT: OK'.format(file))



class Sample36(FrameCountEncodingTest, Base):
    ZIP = 'sample36.zip'

    # Either an issue with the implementation or the file 72610framesi.c3d headers do not define 72610 frames. 
    file_id = [18124, 36220, 72610, 18124, 36220, 72610]
    frame_count = [18124, 36220, 72610, 18124, 36220, 65535]

    @property
    def zip_files(self):
        return ['{}framesf.c3d'.format(c) for c in self.file_id[:3]] +\
               ['{}framesi.c3d'.format(c) for c in self.file_id[3:]]



class Sample31(FrameCountEncodingTest, Base):
    ZIP = 'sample31.zip'

    count = ''
    zip_files = []

if __name__ == '__main__':
    unittest.main()
