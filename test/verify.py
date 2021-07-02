import numpy as np
import warnings
import c3d
from test.zipload import Zipload
from test.base import Base


def count_nan(array):
    return np.sum(np.isnan(array))

##
#
#   Functions evaluting logical expressions on input parameters (returns True/False)
#
##


def array_has_values(array):
    ''' Returns true if at least one dimension in the array is 0
    '''
    return np.prod(np.shape(array)) > 0


def value_in_range(array, min_range, max_range):
    ''' Convert to boolean array where a value is true if it's within the (min, max) range.
    '''
    return (min_range < array) & (array < max_range)


def values_in_range(array, min_range, max_range):
    ''' Returns true if values in the array are within the (min, max) range.
    '''
    return np.all(value_in_range(array, min_range, max_range))

##
#
#   Classes asserting properties on parameters
#
##


class ReadTest():
    ''' Base class testing if a set of pre-defined files can be read with plausible values.
    '''

    def test_read_data(self):

        def check_zipfile(file_path):
            ''' Loads file within a zipfile and execute 'c3d.read_frames()'
            '''
            reader = c3d.Reader(Zipload._get(self.ZIP, file_path))
            nframe_read, nanalog_read = 0, 0

            # Read point frames and analog samples
            for i, points, analog in reader.read_frames(copy=False):
                nframe_read += 1
                nanalog_read += analog.shape[1]

            assert nframe_read == reader.frame_count,\
                "Failed reading file, mismatch in number of frames, read {} expected {}".format(
                 nframe_read, reader.frame_count)
            assert nanalog_read == reader.analog_sample_count,\
                "Failed reading file, mismatch in number of analog samples, read {} expected {}".format(
                 nanalog_read, reader.analog_sample_count)

            print('{} | READ: OK'.format(file))

        # Allow self.zipfiles on form:
        # ['FILE', ..]
        # [('FOLDER', ['FILE', ..])]
        if len(np.shape(self.zip_files)) == 1:
            for file in self.zip_files:
                check_zipfile(file)
        else:
            for folder, files in self.zip_files:
                print('{} | Validating...'.format(folder))
                for file in files:
                    check_zipfile('{}/{}'.format(folder, file))


class WithinRangeTest():
    ''' Base class testing if a set of pre-defined files can be read with plausible values.
    '''

    def test_data_in_range(self):

        min_range, max_range = self.DATA_RANGE

        def check_zipfile(file_path):
            ''' Loads file within a zipfile and execute 'c3d.read_frames()'
            '''
            reader = c3d.Reader(Zipload._get(self.ZIP, file_path))
            self._log(reader)
            npoint = np.zeros((reader.point_used, 5), dtype=np.int64)
            nanalog = np.zeros((reader.analog_used), dtype=np.int64)
            point_min, point_max = 1e10, 1e-10
            analog_min, analog_max = point_min, point_max

            has_point = reader.point_used > 0
            has_analog = reader.analog_used > 0

            # Read point frames and analog samples
            for frame, points, analog in reader.read_frames(copy=False):
                if has_point:
                    npoint += value_in_range(points, min_range, max_range)
                    point_min = np.min(points)
                    point_max = np.max(points)
                if has_analog:
                    nanalog += np.sum(value_in_range(analog, min_range, max_range), axis=1)
                    analog_min = np.min(analog)
                    analog_max = np.max(analog)

            assert np.all(npoint == reader.frame_count), '\n' + \
                'Failed verifying POINT data in range ({}, {}).\n'.format(min_range, max_range) +\
                'Found a total of {} values outside plausible range.\n'.format(
                 np.sum(np.abs(npoint - reader.frame_count), axis=0)) +\
                'Range for data was ({}, {})'.format(point_min, point_max)

            assert np.all(nanalog == reader.analog_sample_count),'\n' + \
                'Failed verifying ANALOG data in range ({}, {}).\n'.format(min_range, max_range) +\
                'Found a total of {} values outside plausible range.\n'.format(
                 np.abs(nanalog - reader.analog_sample_count)) +\
                'Range for data was ({}, {})'.format(analog_min, analog_max)

            print('{} | READ: OK'.format(file))

        # Allow self.zipfiles on form:
        # ['FILE', ..]
        # [('FOLDER', ['FILE', ..])]
        print('----------------------------')
        print(type(self))
        print('----------------------------')
        if len(np.shape(self.zip_files)) == 1:
            for file in self.zip_files:
                check_zipfile(file)
        else:
            for folder, files in self.zip_files:
                print('{} | Validating...'.format(folder))
                for file in files:
                    check_zipfile('{}/{}'.format(folder, file))
        print('DONE')


##
#
#   Functions asserting properties on input parameters
#
##
def array_match_headers(point, analog, reader, label):
    ''' Check point and analog arrays as fetched from load_data(reader), matches the headers in the reader.
    '''
    assert reader.point_used == np.shape(point)[1],\
        'Mismatch in number of POINT samples for file {}, read {} expected {}'.format(
         reader.file_path, np.shape(point)[1], reader.point_used)
    assert reader.analog_used == np.shape(analog)[1],\
        'Mismatch in number of ANALOG samples for file {}, read {} expected {}'.format(
         reader.file_path, np.shape(analog)[1], reader.analog_used)


def point_data_in_range(point, label, min_range, max_range):
    ''' Asserts if all columns in POINT data are within the given range.
    '''
    # Mask in relation to camera bits
    assert array_has_values(point), 'No registered camera bits for file {}'.format(label)
    for i in range(5):
        assert values_in_range(point[:, i], min_range, max_range),\
                "POINT data for column {} was not in range ({}, {}) for file '{}'. Was in range ({}, {})".format(
                i, min_range, max_range, label, np.min(point), np.max(point))


def analog_data_in_range(analog, label, min_range, max_range):
    ''' Asserts if all values in analog are within the given range.
    '''
    # Check ANALOG data
    assert values_in_range(analog, min_range, max_range),\
        "ANALOG data was not in range ({}, {}) for file '{}'. Was in range ({}, {})".format(
         min_range, max_range, label, np.min(analog), np.max(analog))


def equal_headers(test_label, areader, breader, alabel, blabel, areal, breal):
    ''' Ensure headers for data in reader a & b are equivalent.
    '''

    aheader = areader.header
    bheader = breader.header
    assert aheader.parameter_block == bheader.parameter_block, \
        '{}, parameter_block: {} {}, {} {}'.format(
         test_label, alabel, aheader.parameter_block, blabel, bheader.parameter_block)
    assert aheader.parameter_block == bheader.parameter_block, \
        '{}, data_block: {} {}, {} {}'.format(
         test_label, alabel, aheader.data_block, blabel, bheader.data_block)
    assert aheader.point_count == bheader.point_count, \
        '{}, point_count: {} {}, {} {}'.format(
         test_label, alabel, aheader.point_count, blabel, bheader.point_count)
    assert aheader.analog_count == bheader.analog_count, \
        '{}, analog_count: {} {}, {} {}'.format(
         test_label, alabel, aheader.point_count, blabel, bheader.point_count)
    assert aheader.first_frame == bheader.first_frame, \
        '{}, first_frame: {} {}, {} {}'.format(
         test_label, alabel, aheader.first_frame, blabel, bheader.first_frame)
    assert aheader.last_frame == bheader.last_frame, \
        '{}, last_frame: {} {}, {} {}'.format(
         test_label, alabel, aheader.last_frame, blabel, bheader.last_frame)
    assert aheader.analog_per_frame == bheader.analog_per_frame, \
        '{}, analog_per_frame: {} {}, {} {}'.format(
         test_label, alabel, aheader.analog_per_frame, blabel, bheader.analog_per_frame)
    assert aheader.frame_rate == bheader.frame_rate, \
        '{}, frame_rate: {} {}, {} {}'.format(
         test_label, alabel, aheader.frame_rate, blabel, bheader.frame_rate)
    assert aheader.max_gap == bheader.max_gap, \
        '{}, max_gap: {} {}, {} {}'.format(
         test_label, alabel, aheader.max_gap, blabel, bheader.max_gap)
    assert aheader.max_gap == bheader.max_gap, \
        '{}, max_gap: {} {}, {} {}'.format(
         test_label, alabel, aheader.max_gap, blabel, bheader.max_gap)
    assert aheader.long_event_labels == bheader.long_event_labels, \
        '{}, long_event_labels: {} {}, {} {}'.format(
         test_label, alabel, aheader.long_event_labels, blabel, bheader.long_event_labels)

    event_mismatch = max(0, bheader.event_count - aheader.event_count)
    for i in range(aheader.event_count):
        event_label = aheader.event_labels[i]
        if event_label in bheader.event_labels:
            lindex = bheader.event_labels.tolist().index(event_label)
            assert aheader.event_disp_flags[i] == bheader.event_disp_flags[lindex], \
                '{}, event_disp_flag {}: {} {}, {} {}'.format(
                 test_label, event_label, alabel, aheader.event_disp_flags[i], blabel,
                 bheader.event_disp_flags[lindex])
            assert np.isclose(aheader.event_timings[i], bheader.event_timings[lindex], atol=1e-7), \
                '{}, event_timings {}: {} {}, {} {}'.format(
                 test_label, event_label, alabel, aheader.event_timings[i], blabel, bheader.event_timings[lindex])
        else:
            event_mismatch += 1

    # Validate event differences, up to a few labels can be mismatched
    err_str = '{}, label missmatch in event_block. File {} had {} and {} had {} with no match'.format(
               test_label, alabel, [lab for lab in aheader.event_labels if lab not in bheader.event_labels],
               blabel, [lab for lab in bheader.event_labels if lab not in aheader.event_labels])
    if event_mismatch > 0:
        if event_mismatch <= 2:
            warnings.warn(err_str, ImportWarning)
        else:
            assert False, err_str

    if areal:
        assert aheader.scale_factor < 0.0, \
            '{}, {} scale_factor: expected {} < 0'.format(test_label, alabel, aheader.scale_factor)
    else:
        assert aheader.scale_factor > 0.0, \
            '{}, {} scale_factor: expected 0 < {}'.format(test_label, alabel, aheader.scale_factor)
    if breal:
        assert bheader.scale_factor < 0.0, \
            '{}, {} scale_factor: expected {} < 0'.format(test_label, blabel, bheader.scale_factor)
    else:
        assert bheader.scale_factor > 0.0, \
            '{}, {} scale_factor: expected 0 < {}'.format(test_label, blabel, bheader.scale_factor)


def data_is_equal(areader, breader, alabel, blabel):
    ''' Ensure data in reader a & b are equivalent.
    '''
    # Number of scale factors data can deviate
    equal_scale_fac = 1.01

    # Check frame count
    assert areader.frame_count == breader.frame_count, 'Expected frame count to be equal was {} and {}'.format(
           areader.frame_count, breader.frame_count)
    # Check point count
    assert areader.point_used == breader.point_used,\
        'Expected per frame point sample count to be equal was {} and {}'.format(
         areader.point_used, breader.point_used)
    # Check analog sample count
    assert areader.analog_sample_count == breader.analog_sample_count,\
        'Expected analog sample count to be equal was {} and {}'.format(
         areader.analog_sample_count, breader.analog_sample_count)
    assert np.abs(areader.point_scale) == np.abs(breader.point_scale),\
        'Expected coordinate scale to be equal was {} and {}'.format(
         np.abs(areader.point_scale), np.abs(breader.point_scale))

    # Fetch file params/data
    frame_count = areader.frame_count
    analog_count = areader.analog_sample_count
    apoint, aanalog = Base.load_data(areader)
    bpoint, banalog = Base.load_data(breader)

    apoint = np.reshape(apoint, (-1, 5))
    bpoint = np.reshape(bpoint, (-1, 5))

    avalid = apoint[:, 3] >= 0
    bvalid = bpoint[:, 3] >= 0
    valid_diff = np.sum(np.logical_xor(avalid, bvalid))
    assert valid_diff == 0, '\n' +\
        'Error in number of valid samples between {} and {}.\n'.format(alabel, blabel) +\
        'Total number of validation mismatches: {} of {}'.format(valid_diff, len(avalid))

    # Only compare valid point data
    valid = avalid
    apoint = apoint[valid]
    bpoint = bpoint[valid]

    tot_points = len(apoint)
    tot_analog = areader.analog_used * analog_count

    # Compare point data (coordinates)
    c = ['X', 'Y', 'Z']
    # Tolerance (allow scale x integer rounding error)
    atol = equal_scale_fac * abs(areader.point_scale)
    for i in range(3):
        was_close = np.isclose(apoint[:, i], bpoint[:, i], atol=atol)
        axis_notclose = tot_points - np.sum(was_close)
        assert axis_notclose == 0, '\n' +\
            'Mismatched coordinates on {} axis between {} and {}.\n'.format(c[i], alabel, blabel) +\
            'Samples with absolute difference larger then {:0.4f}: {} of {}.\n'.format(
            atol, axis_notclose, tot_points) +\
            'Maximum difference: {}'.format(np.max(np.abs(apoint[:, i] - bpoint[:, i])))

    # Word 4 (residual + camera bits)
    residual_diff = tot_points - np.sum(np.isclose(apoint[:, 3], bpoint[:, 3]))
    cam_close = np.isclose(apoint[:, 4], bpoint[:, 4])
    cam_diff_non_equal = tot_points - np.sum(cam_close)

    # Camera bit errors (warn if non identical, allow 1 cam bit diff, might be bad DEC implementation, or bad data)
    if cam_diff_non_equal > 0:
        #print(apoint[~cam_close, 4])
        #print(bpoint[~cam_close, 4])
        cam_close = np.isclose(apoint[:, 4], bpoint[:, 4], atol=1.001)
        cam_diff = tot_points - np.sum(cam_close)
        assert cam_diff == 0, '\n' + \
            'Mismatch in camera bit flags between {} and {}.\n'.format(alabel, blabel) +\
            'Number of samples with flag differences larger then 1: {} of {}'.format(cam_diff, tot_points)
        err_str = '\n' + \
            'Mismatch in camera bit flags between {} and {}.\n'.format(alabel, blabel) +\
            'Number of samples with flag difference of 1: {} of {}'.format(cam_diff_non_equal, tot_points)
        warnings.warn(err_str, RuntimeWarning)
    # Residual assert
    assert residual_diff == 0, '\n' +\
        'Error in sample residuals between {} and {}.\n'.format(alabel, blabel) +\
        'Total number of failed samples: {} of {}'.format(residual_diff, tot_points)

    # Compare analog
    was_close = np.isclose(aanalog, banalog)
    analog_notclose = tot_analog - np.sum(was_close)
    assert analog_notclose == 0, '\n' + \
        'Mismatched analog samples between {} and {}.\n'.format(alabel, blabel) +\
        'Total number of failed samples: {} of {}.\n'.format(analog_notclose, tot_analog) +\
        'Largest absolute difference: {}.'.format(np.max(np.abs(aanalog - banalog)))
