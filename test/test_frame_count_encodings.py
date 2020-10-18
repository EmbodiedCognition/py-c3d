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



class AnalogSampleCountEncodingTest():
    ''' Base class testing if sample count for analog data can be read when encoded differently.
    '''

    def test_b_read(self):

        print('----------------------------')
        print(type(self))
        print('----------------------------')

        for file, sample_count in zip(self.zip_files, self.sample_count):
            reader = c3d.Reader(Zipload._get(self.ZIP, file))
            self._log(reader)

            # Verify file count
            assert reader.analog_sample_count == sample_count,\
                   'Wrong analog sample count read from file {}/{}. Expected {} was {}'.format(
                   self.ZIP, file, sample_count, reader.analog_sample_count)
            print('{} | SAMPLE_COUNT: OK'.format(file))


class Sample31(FrameCountEncodingTest, Base):
    ''' Test to evaluate if two files with large number of frames are read correctly.
    '''
    ZIP = 'sample31.zip'

    frame_count = [73285, 72610]
    zip_files = ['large01.c3d', 'large02.c3d']


class Sample36(FrameCountEncodingTest, Base):
    ''' Test to evaluate if files with large number of frames are read correctly.
    '''
    ZIP = 'sample36.zip'

    # The file 72610framesi.c3d parameter headers do not define 72610 frames.
    # Can be verified by using the MLS viewer: https://www.c3d.org/apps/MLSviewer_setup.exe
    file_id = [18124, 36220, 72610, 18124, 36220, 72610]
    frame_count = [18124, 36220, 72610, 18124, 36220, 65535]

    @property
    def zip_files(self):
        return ['{}framesf.c3d'.format(c) for c in self.file_id[:3]] +\
               ['{}framesi.c3d'.format(c) for c in self.file_id[3:]]


class Sample19(FrameCountEncodingTest, AnalogSampleCountEncodingTest, Base):
    ''' Test to evaluate if files with large number of analog samples are read correctly.
    '''
    ZIP = 'sample19.zip'

    frame_count = [34672]
    sample_count = [37445760]
    zip_files = ['sample19/sample19.c3d']


if __name__ == '__main__':
    unittest.main()

if __name__ == '__main__':
    unittest.main()
