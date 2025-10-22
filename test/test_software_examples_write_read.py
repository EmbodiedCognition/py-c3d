''' Tests
'''

import c3d
import unittest
import os
import test.verify as verify
import numpy as np
from test.base import Base
from test.zipload import Zipload, TEMP

# Run all examples on all copy tests
MINIMAL_TEST = True


def verify_read_write(zip, file_path, proc_type='INTEL', real=True, cpy_mode='copy'):
    ''' Compare read write ouput to original read file.
    '''
    assert cpy_mode != 'copy_header', "Copy mode not supported for verification"
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
        if cpy_mode == 'convert':
            # Compare writer instead
            verify.equal_headers(test_id, writer, B, aname, bname, real, real)
        else:
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

    if frames == 1:
        for _ in range(frames):
            writer.add_frames((np.random.randn(len(labels), 5), ()))
    elif frames > 1:
        new_frames = []
        for __ in range(frames):
            new_frames.append((np.random.randn(len(labels), 5), ()))
        writer.add_frames(new_frames)
    
    writer.set_point_labels(labels)
    writer.set_analog_labels(None)
    return writer

class GeneratedExamples(Base):
    
    def test_error_writing_no_frames(self):
        """ Verify no frames generates a runtime error (illegal to write empty file).
        """
        writer = c3d.Writer(point_rate=200)
        writer.set_point_labels(None)
        writer.set_analog_labels(None)

        tmp_path = os.path.join(TEMP, 'no-frames.c3d')

        try:
            with open(tmp_path, 'wb') as h:
                writer.write(h)
            assert False, "Expected RuntimeError writing empty file."
        except RuntimeError as e:
            pass  # RuntimeError writing empty file
        
    def test_error_adding_invalid_frames(self):
        """ Verify no frames generates a runtime error (illegal to write empty file).
        """
        writer = c3d.Writer(point_rate=200)
        writer.set_point_labels(None)
        writer.set_analog_labels(None)

        with self.assertRaises(ValueError):
            writer.add_frames(((), ()),)
            
        with self.assertRaises(ValueError):
            # Invalid, to few dims
            writer.add_frames(np.random.randn(3, 5))

        with self.assertRaises(ValueError):
            # Invalid, expect first dim to contain 2 elements
            writer.add_frames(np.random.randn(3, 13, 5))

        with self.assertRaises(ValueError):
            # Mismatch due to invalid second dim
            writer.add_frames(np.random.randn(4, 3, 27, 5))
            
        with self.assertRaises(ValueError):
            # Raise due to analog rate mismatch (invalid 4th dim)
            writer.add_frames(np.random.randn(4, 2, 17, 5))

        with self.assertRaises(ValueError):
            # Raise due to extra dimensions
            writer.add_frames(np.random.randn(5, 4, 2, 7, 5))
        
    def test_writing_single_point_frame(self):
        """ Verify writing a file with a single frame.
        """
        labels = ['RFT1', 'RFT2', 'RFT3', 'RFT4', 'LFT1', 'LFT2', 'LFT3', 'LFT4',
                  'RSK1', 'RSK2', 'RSK3', 'RSK4', 'LSK1', 'LSK2', 'LSK3', 'LSK4',
                  'RTH1', 'RTH2', 'RTH3', 'RTH4', 'LTH1', 'LTH2', 'LTH3', 'LTH4'
                  ]
        writer = create_dummy_writer(labels)

        tmp_path = os.path.join(TEMP, 'single-point-frame.c3d')
        with open(tmp_path, 'wb') as h:
            writer.write(h)

        with open(tmp_path, 'rb') as handle:
            B = c3d.Reader(handle)
            
            verify.equal_headers("test_writing_single_point_frame", writer, B, "Original", "WriteRead", True, True)

            for a, b in zip(labels, B.get('POINT.LABELS').string_array):
                assert a == b, "Label missmatch"

    def test_writing_multiple_point_frame(self):
        """ Verify writing a file with a single frame.
        """
        num_frames = 11
        writer = create_dummy_writer(frames=num_frames)

        tmp_path = os.path.join(TEMP, 'single-point-frame.c3d')
        with open(tmp_path, 'wb') as h:
            writer.write(h)

        with open(tmp_path, 'rb') as handle:
            B = c3d.Reader(handle)
            assert B.frame_count == num_frames, "Expected {} point frames was {}".format(num_frames, B.frame_count)
            verify.equal_headers("test_writing_multiple_point_frame", writer, B, "Original", "WriteRead", True, True)
                
    def test_writing_analog_frames(self):
        """ Verify writing a file with a single frame.
        """
        labels = ['RFT1', 'RFT2', 'RFT3', 'RFT4', 'LFT1', 'LFT2', 'LFT3', 'LFT4',
                  'RSK1', 'RSK2', 'RSK3', 'RSK4', 'LSK1', 'LSK2', 'LSK3', 'LSK4',
                  'RTH1', 'RTH2', 'RTH3', 'RTH4', 'LTH1', 'LTH2', 'LTH3', 'LTH4'
                  ]
        writer = c3d.Writer(point_rate=12, analog_rate=36)

        # Single frame input
        for __ in range(5):
            writer.add_frames(((), np.random.randn(len(labels), writer.analog_per_frame),))
        
        # Twin frame input
        new_frames = [((), np.random.randn(len(labels), writer.analog_per_frame),), 
                      ((), np.random.randn(len(labels), writer.analog_per_frame),)]
        writer.add_frames(new_frames)

        # Multi frame input
        new_frames = []
        for __ in range(5):
            new_frames.append(((), np.random.randn(len(labels), writer.analog_per_frame),))
        writer.add_frames(new_frames)
        
        writer.set_point_labels(None)
        writer.set_analog_labels(labels)

        tmp_path = os.path.join(TEMP, 'single-analog-frame.c3d')
        with open(tmp_path, 'wb') as h:
            writer.write(h)

        with open(tmp_path, 'rb') as handle:
            B = c3d.Reader(handle)
            
            verify.equal_headers("test_writing_single_point_frame", writer, B, "Original", "WriteRead", True, True)

            assert B.analog_sample_count == 12 * writer.analog_per_frame, "Expected {} samples was {}".format(
                B.analog_sample_count, 12 * writer.analog_per_frame)

            for a, b in zip(labels, B.get('ANALOG.LABELS').string_array):
                assert a == b, "Label missmatch"

    def test_write_long_str_param(self):
        writer = create_dummy_writer()
        grp = writer.add_group(66, "UnittestGroup", "Generated for unittest purposes")
        
        num_param = 10
        data = []
        for index in range(255 * num_param):
            value = "Str:" + format(index, '08d')
            assert len(value) == 12, "Unittest is invalid, expected string with length 12"
            data.append(value)

        grp.add_str("LongString", "String spanning %i parameters." % num_param, data)

        tmp_path = os.path.join(TEMP, 'long_str_parameter.c3d')
        with open(tmp_path, 'wb') as h:
            writer.write(h)

        with open(tmp_path, 'rb') as handle:
            B = c3d.Reader(handle)
            
            verify.equal_headers("test_write_long_str_param", writer, B, "Original", "WriteRead", True, True)

            str_index = 0
            for index in range(0, num_param):
                postfix = "" if index == 0 else str(index + 1)
                param_name = "UnittestGroup.LongString" + postfix
                agrp = writer.get(param_name)
                bgrp = B.get(param_name)

                # Verify string parameter matches initial input and between read/write
                read_data = bgrp.string_array
                assert np.array_equal(agrp.string_array, read_data), "Expected string data to match"
                assert np.array_equal(data[str_index:str_index + len(read_data)], read_data), "Expected string data to match"
                str_index += len(read_data)

    def test_write_long_float_param(self):
        writer = create_dummy_writer()
        grp = writer.add_group(66, "UnittestGroup", "Generated for unittest purposes")
        
        num_param = 10

        data = np.random.randn(2, 2, 255 * num_param).astype(np.float32)
        grp.add_array("LongFltArray", "Float array spanning {} parameters.".format(num_param), data)
        # Fortran to C order for comparison
        data = data.reshape(data.shape[::-1])

        tmp_path = os.path.join(TEMP, 'long_flt_parameter.c3d')
        with open(tmp_path, 'wb') as h:
            writer.write(h)

        with open(tmp_path, 'rb') as handle:
            B = c3d.Reader(handle)
            
            verify.equal_headers("test_write_long_float_param", writer, B, "Original", "WriteRead", True, True)

            prm_index = 0
            for index in range(0, num_param):
                postfix = "" if index == 0 else str(index + 1)
                param_name = "UnittestGroup.LongFltArray" + postfix
                agrp = writer.get(param_name)
                bgrp = B.get(param_name)
                assert bgrp is not None, "Parameter {} was not written to the file".format(param_name)

                # Verify string parameter matches initial input and between read/write
                read_data = bgrp.float32_array
                input_data = data[prm_index:prm_index + len(read_data)]
                assert np.array_equal(agrp.float32_array, read_data), "Expected array to match between Reader and Writer"
                assert np.array_equal(input_data, read_data), "Expected array data to match the input data"
                prm_index += len(read_data)

class Sample00(Base):

    ZIP = 'sample00.zip'
    zip_files = \
        [
         ('Advanced Realtime Tracking GmbH', ['arthuman-sample.c3d', 'arthuman-sample-fingers.c3d']),
         ('Codamotion', ['codamotion_gaitwands_19970212.c3d', 'codamotion_gaitwands_20150204.c3d']),
         ('Cometa Systems', ['EMG Data Cometa.c3d']),
         ('Innovative Sports Training', ['Gait with EMG.c3d', 'Static Pose.c3d']),
         ('Motion Analysis Corporation', ['Sample_Jump2.c3d', 'Walk1.c3d']),
         ('NexGen Ergonomics', ['test1.c3d']),
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
        if MINIMAL_TEST:
            zip_files = [self.zip_files[-1]]
        else:
            zip_files = self.zip_files
        for folder, files in zip_files:
            print('{} | Validating...'.format(folder))
            for file in files:
                verify_read_write(self.ZIP, '{}/{}'.format(folder, file), cpy_mode='shallow_copy')
        print('... OK')
        print('DONE')
        
    def test_read_write_convert_examples(self):
        ''' Compare data written by a 'convert' `Reader` to data in the original file
        '''

        print('----------------------------')
        print('Convert')
        print('----------------------------')
        if MINIMAL_TEST:
            zip_files = [self.zip_files[-1]]
        else:
            zip_files = self.zip_files
        for folder, files in zip_files:
            print('{} | Validating...'.format(folder))
            for file in files:
                verify_read_write(self.ZIP, '{}/{}'.format(folder, file), cpy_mode='convert')
        print('... OK')
        print('DONE')
        
    def test_read_write_header_examples(self):
        ''' Compare data written by a 'copy_header' only `Writer` to data in the original file
        '''

        print('----------------------------')
        print('copy_header')
        print('----------------------------')
        if MINIMAL_TEST:
            zip_files = [self.zip_files[-1]]
        else:
            zip_files = self.zip_files
        for folder, files in zip_files:
            print('{} | Validating...'.format(folder))
            for file in files:
                A = c3d.Reader(Zipload._get(self.ZIP, '{}/{}'.format(folder, file)))
                writer = A.to_writer('copy_header')
                verify.equal_headers('test_read_write_header_examples', A, writer, 'Original', 'Writer Copy', True, True)
        print('... OK')
        print('DONE')

    def test_read_write_copy_metadata_examples(self):
        ''' Compare data written by a 'copy_metadata' only `Writer` to data in the original file
        '''

        print('----------------------------')
        print('copy_metadata')
        print('----------------------------')
        if MINIMAL_TEST:
            zip_files = [self.zip_files[-1]]
        else:
            zip_files = self.zip_files
        for folder, files in zip_files:
            print('{} | Validating...'.format(folder))
            for file in files:
                A = c3d.Reader(Zipload._get(self.ZIP, '{}/{}'.format(folder, file)))
                writer = A.to_writer('copy_metadata')
                verify.equal_headers('test_read_write_copy_metadata_examples', A, writer, 'Original', 'Writer Copy', True, True)
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
