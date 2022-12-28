''' Tests
'''

import c3d
import unittest
import os
import test.verify as verify
import numpy as np
from test.base import Base
from test.zipload import Zipload, TEMP


def verify_read_write(zip, file_path, proc_type='INTEL', real=True, cpy_mode='copy'):
    ''' Compare read write ouput to original read file.
    '''
    A = c3d.Reader(Zipload._get(zip, file_path))

    if proc_type != 'INTEL':
        # Deep copy for data in non-Intel files is not supported
        cpy_mode = 'shallow_copy'
    
    writer = A.to_writer(cpy_mode)

    tmp_path = os.path.join(TEMP, 'write_test.c3d')
    with open(tmp_path, 'wb') as handle:
        writer.write(handle)

    aname = 'Original'
    bname = 'WriteRead'
    test_id = '{} write read test'.format(proc_type)

    with open(tmp_path, 'rb') as handle:
        B = c3d.Reader(handle)
        verify.equal_headers(test_id, A, B, aname, bname, real, real)
        verify.data_is_equal(A, B, aname, bname)


def create_dummy_writer(labels=None, frames=1):
    """ Create a dummy writer populated with the given number of random frames and labels (to not be empty).
    """
    writer = c3d.Writer(point_rate=200)
    if labels is None:
        labels = ['RFT1', 'RFT2', 'RFT3', 'RFT4', 'LFT1', 'LFT2', 'LFT3', 'LFT4',
                  'RSK1', 'RSK2', 'RSK3', 'RSK4', 'LSK1', 'LSK2', 'LSK3', 'LSK4',
                  'RTH1', 'RTH2', 'RTH3', 'RTH4', 'LTH1', 'LTH2', 'LTH3', 'LTH4'
                  ]

    if frames > 0:
        for _ in range(frames):
            writer.add_frames((np.random.randn(len(labels), 5), ()))
    
    writer.set_point_labels(labels)
    writer.set_analog_labels(None)
    return writer

class GeneratedExamples(Base):
    
    def test_error_writing_no_frames(self):
        """ Verify no frames generates a runtime error (illegal to write empty file).
        """
        writer = c3d.Writer(point_rate=200)
        #for _ in range(1):
        #    writer.add_frames((np.random.randn(24, 5), ()))
        #writer.set_point_labels(['RFT1', 'RFT2', 'RFT3', 'RFT4', 'LFT1', 'LFT2', 'LFT3', 'LFT4',
        #                        'RSK1', 'RSK2', 'RSK3', 'RSK4', 'LSK1', 'LSK2', 'LSK3', 'LSK4',
        #                        'RTH1', 'RTH2', 'RTH3', 'RTH4', 'LTH1', 'LTH2', 'LTH3', 'LTH4'
        #                        ])
        writer.set_point_labels(None)
        writer.set_analog_labels(None)

        tmp_path = os.path.join(TEMP, 'no-frames.c3d')

        try:
            with open(tmp_path, 'wb') as h:
                writer.write(h)
            assert False, "Expected RuntimeError writing empty file."
        except RuntimeError as e:
            pass  # RuntimeError writing empty file
        
    def test_writing_single_frame(self):
        """ Verify writing a file with a single frame.
        """
        labels = ['RFT1', 'RFT2', 'RFT3', 'RFT4', 'LFT1', 'LFT2', 'LFT3', 'LFT4',
                  'RSK1', 'RSK2', 'RSK3', 'RSK4', 'LSK1', 'LSK2', 'LSK3', 'LSK4',
                  'RTH1', 'RTH2', 'RTH3', 'RTH4', 'LTH1', 'LTH2', 'LTH3', 'LTH4'
                  ]
        writer = create_dummy_writer(labels)

        tmp_path = os.path.join(TEMP, 'single-frame.c3d')
        with open(tmp_path, 'wb') as h:
            writer.write(h)

        with open(tmp_path, 'rb') as handle:
            B = c3d.Reader(handle)
            
            verify.equal_headers("test_writing_single_frame", writer, B, "Original", "WriteRead", True, True)

            for a, b in zip(labels, B.get('POINT.LABELS').string_array):
                assert a == b, "Label missmatch"
        

    def test_write_long_param(self):
        writer = create_dummy_writer()
        grp = writer.add_group(66, "UnittestGroup", "Generated for unittest purposes")
        
        num_param = 10
        data = []
        for index in range(255 * num_param):
            value = "Str:" + format(index, '08d')
            assert len(value) == 12, "Unittest is invalid, expected string with length 12"
            data.append(value)

        grp.add_str("LongString", "String spanning %i parameters." % num_param, data)

        tmp_path = os.path.join(TEMP, 'long_parameter.c3d')
        with open(tmp_path, 'wb') as h:
            writer.write(h)

        with open(tmp_path, 'rb') as handle:
            B = c3d.Reader(handle)
            
            verify.equal_headers("test_write_long_param", writer, B, "Original", "WriteRead", True, True)

            for index in range(0, num_param):
                postfix = "" if index == 0 else str(index + 1)
                param_name = "UnittestGroup.LongString" + postfix
                agrp = writer.get(param_name)
                bgrp = B.get(param_name)
                assert np.array_equal(agrp.string_array, bgrp.string_array), "Expected string data to match"


class Sample00(Base):

    ZIP = 'sample00.zip'
    zip_files = \
        [
         #('Advanced Realtime Tracking GmbH', ['arthuman-sample.c3d', 'arthuman-sample-fingers.c3d']),
         #('Codamotion', ['codamotion_gaitwands_19970212.c3d', 'codamotion_gaitwands_20150204.c3d']),
         #('Cometa Systems', ['EMG Data Cometa.c3d']),
         #('Innovative Sports Training', ['Gait with EMG.c3d', 'Static Pose.c3d']),
         #('Motion Analysis Corporation', ['Sample_Jump2.c3d', 'Walk1.c3d']),
         #('NexGen Ergonomics', ['test1.c3d']),
         # Vicon files are weird, uses non-standard encodings. Walking01.c3d contain nan values.
         ('Vicon Motion Systems', ['pyCGM2 lower limb CGM24 Walking01.c3d', 'TableTennis.c3d']),
        ]

    def test_read_write_copy_examples(self):
        ''' Compare data copied through the `Writer` class to data in the original file
        '''

        print('----------------------------')
        print(type(self))
        print('----------------------------')
        for folder, files in self.zip_files:
            print('{} | Validating...'.format(folder))
            for file in files:
                verify_read_write(self.ZIP, '{}/{}'.format(folder, file))
            print('... OK')
        print('DONE')

    def test_read_write_shallow_copy_examples(self):
        ''' Compare shallow copied data written by the `Writer` class to data in the original file
        '''

        print('----------------------------')
        print('Shallow-copy')
        print('----------------------------')
        folder, files = self.zip_files[-1]
        print('{} | Validating...'.format(folder))
        for file in files:
            verify_read_write(self.ZIP, '{}/{}'.format(folder, file), cpy_mode='shallow_copy')
        print('... OK')
        print('DONE')

class Sample01(Base):

    ZIP = 'sample01.zip'
    zip_files = \
        [
         ('Eb015pi.c3d', 'INTEL', False),
         ('Eb015pr.c3d', 'INTEL', True),
         ('Eb015vi.c3d', 'DEC', False),
         ('Eb015vr.c3d', 'DEC', True),
         ('Eb015si.c3d', 'SGI', False),
         ('Eb015sr.c3d', 'SGI', True),
        ]

    def test_read_write_examples(self):
        ''' Compare write ouput to original read
        '''
        print('----------------------------')
        print(type(self))
        print('----------------------------')
        for (file, proc, is_real) in self.zip_files:
            print('{} | Validating...'.format(file))
            verify_read_write(self.ZIP, file, proc, is_real)
            print('... OK')
        print('Done.')



if __name__ == '__main__':
    unittest.main()
