import unittest
import numpy as np
import warnings
from test.zipload import Zipload


class Base(unittest.TestCase):
    def setUp(self):
        Zipload.download()


    def _log(self, r):
        return
        print(r.header)
        items = ((k, v) for k, v in r.groups.items() if isinstance(k, str))
        fmt = '{0.name:>14s}:{1.name:<14s} {1.desc:36s} {2}'
        for _, g in sorted(items):
            for _, p in sorted(g.params.items()):
                value = None
                if p.bytes_per_element == 4:
                    if p.dimensions:
                        value = p.float_array
                    else:
                        value = p.float_value
                if p.bytes_per_element == 2:
                    if p.dimensions:
                        value = p.int16_array
                    else:
                        value = p.int16_value
                if p.bytes_per_element == 1:
                    if p.dimensions:
                        value = p.int8_array
                    else:
                        value = p.int8_value
                if p.bytes_per_element == -1:
                    if len(p.dimensions) > 1:
                        value = [s.strip() for s in p.string_array]
                    else:
                        value = p.string_value
                print(fmt.format(g, p, value))


    def compare_header(test_label, areader, breader, alabel, blabel, areal, breal):
        ''' Ensure headers for data in reader a & b are equivalent.
        '''

        aheader = areader.header
        bheader = breader.header
        assert aheader.parameter_block == bheader.parameter_block, \
            '{}, parameter_block: {} {}, {} {}'.format(test_label,
            alabel, aheader.parameter_block, blabel, bheader.parameter_block)
        assert aheader.parameter_block == bheader.parameter_block, \
            '{}, data_block: {} {}, {} {}'.format(test_label,
            alabel, aheader.data_block, blabel, bheader.data_block)
        assert aheader.point_count == bheader.point_count, \
            '{}, point_count: {} {}, {} {}'.format(test_label,
            alabel, aheader.point_count, blabel, bheader.point_count)
        assert aheader.analog_count == bheader.analog_count, \
            '{}, analog_count: {} {}, {} {}'.format(test_label,
            alabel, aheader.point_count, blabel, bheader.point_count)
        assert aheader.first_frame == bheader.first_frame, \
            '{}, point_count: {} {}, {} {}'.format(test_label,
            alabel, aheader.first_frame, blabel, bheader.first_frame)
        assert aheader.last_frame == bheader.last_frame, \
            '{}, last_frame: {} {}, {} {}'.format(test_label,
            alabel, aheader.last_frame, vbheader.last_frame)
        assert aheader.analog_per_frame == bheader.analog_per_frame, \
            '{}, analog_per_frame: {} {}, {} {}'.format(test_label,
            alabel, aheader.analog_per_frame, blabel, bheader.analog_per_frame)
        assert aheader.frame_rate == bheader.frame_rate, \
            '{}, frame_rate: {} {}, {} {}'.format(test_label,
            alabel, aheader.frame_rate, blabel, bheader.frame_rate)
        assert aheader.max_gap == bheader.max_gap, \
            '{}, max_gap: {} {}, {} {}'.format(test_label,
            alabel, aheader.max_gap, blabel, bheader.max_gap)
        assert aheader.max_gap == bheader.max_gap, \
            '{}, max_gap: {} {}, {} {}'.format(test_label,
            alabel, aheader.max_gap, blabel, bheader.max_gap)
        assert aheader.long_event_labels == bheader.long_event_labels, \
            '{}, long_event_labels: {} {}, {} {}'.format(test_label,
            alabel, aheader.long_event_labels, blabel, bheader.long_event_labels)

        event_mismatch = max(0, bheader.event_count - aheader.event_count)
        for i in range(aheader.event_count):
            event_label = aheader.event_labels[i]
            if event_label in bheader.event_labels:
                lindex = bheader.event_labels.index(event_label)
                assert aheader.event_disp_flags[i] == bheader.event_disp_flags[lindex], \
                    '{}, event_disp_flag {}: {} {}, {} {}'.format(test_label, event_label,
                    alabel, aheader.event_disp_flags[i], blabel, bheader.event_disp_flags[lindex])
                assert np.isclose(aheader.event_timings[i], bheader.event_timings[lindex], atol=1e-7), \
                    '{}, event_timings {}: {} {}, {} {}'.format(test_label, event_label,
                    alabel, aheader.event_timings[i], blabel, bheader.event_timings[lindex])
            else:
                event_mismatch += 1

        # Validate event differences, up to a few labels can be mismatched
        err_str = '''{}, label missmatch in event_block. File {} had {} and {} had {} with no match'''.format(
            test_label, alabel, [l for l in aheader.event_labels if l not in bheader.event_labels],
            blabel, [l for l in bheader.event_labels  if l not in aheader.event_labels])
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


    def load_data(reader):
        ''' Fetch point and analog data arrays
        '''

        # Fetch sample rate parameters
        first_frame = reader.first_frame
        nframe = reader.frame_count
        npoint = reader.header.point_count
        nanalog_count = reader.analog_sample_count
        nanalog_channel = reader.analog_used
        nanalog_per_frame_samples = reader.analog_per_frame

        # Generate data arrays
        point_frames = np.zeros([nframe, 5, npoint], dtype=np.float64)
        analog_frames = np.zeros([nanalog_count, nanalog_channel], dtype=np.float64)

        # Start reading POINT and ANALOG blocks
        for i, points, analog in reader.read_frames(copy=False):
            # Extract columns 0:5
            index = i - first_frame
            aindex = index * nanalog_per_frame_samples
            point_frames[index] = points.T
            analog_frames[aindex:aindex+nanalog_per_frame_samples] = analog.T

        # Return data frames
        return point_frames, analog_frames

    def compare_data(areader, breader, alabel, blabel):
        ''' Ensure data in reader a & b are equivalent.
        '''
        # Number of scale factors data can deviate
        equal_scale_fac = 2.01

        # Check frame count
        assert areader.frame_count == breader.frame_count, 'Expected frame count to be equal was {} and {}'.format(\
               areader.frame_count, breader.frame_count)
        # Check point count
        assert areader.point_used == breader.point_used,\
               'Expected per frame point sample count to be equal was {} and {}'.format(\
               areader.point_used, breader.point_used)
        # Check analog sample count
        assert areader.analog_sample_count == breader.analog_sample_count,\
               'Expected analog sample count to be equal was {} and {}'.format(\
               areader.analog_sample_count, breader.analog_sample_count)
        assert np.abs(areader.point_scale) == np.abs(breader.point_scale),\
                'Expected coordinate scale to be equal was {} and {}'.format(\
                np.abs(areader.point_scale), np.abs(breader.point_scale))

        # Fetch file params/data
        frame_count = areader.frame_count
        analog_count = areader.analog_sample_count
        apoint, aanalog = Base.load_data(areader)
        bpoint, banalog = Base.load_data(breader)

        # Debug, diff
        #mask = np.abs(apoint - bpoint) > 1e-5
        #print(apoint[mask])
        #print(bpoint[mask])

        nsampled_coordinates = areader.point_used * areader.frame_count
        nsampled_analog = areader.analog_used * analog_count

        # Compare point data (coordinates)
        c = ['X', 'Y', 'Z']
        for i in range(3):
            axis_diff = nsampled_coordinates - np.sum(np.isclose(apoint[:, 0], bpoint[:, 0],
                atol=equal_scale_fac*abs(areader.point_scale)))
            assert axis_diff == 0, \
                'Mismatched coordinates on {} axis for {} and {}, number of sampled diff: {} of {}'.format(
                c[i], alabel, blabel, axis_diff, nsampled_coordinates)
        # Word 4 (residual + camera bits)
        residual_diff = nsampled_coordinates - np.sum(np.isclose(apoint[:, 3], bpoint[:, 3]))
        cam_diff = nsampled_coordinates - np.sum(np.isclose(apoint[:, 4], bpoint[:, 4], atol=1.001))
        cam_diff_non_equal = nsampled_coordinates - np.sum(np.isclose(apoint[:, 4], bpoint[:, 4]))

        # Cam bit errors (warn if non identical, allow 1 cam bit diff, might be bad DEC implementation, or bad data)
        if cam_diff_non_equal > 0:
            assert cam_diff == 0, 'Mismatch error in camera bit flags for {} and {}, number of samples with flag diff:\
            {} of {}'.format(alabel, blabel, cam_diff, nsampled_coordinates)
            err_str = 'Mismatch in camera bit flags between {} and {}, number of samples with flag diff:\
                {} of {}'.format(alabel, blabel, cam_diff_non_equal, nsampled_coordinates)
            warnings.warn(err_str, RuntimeWarning)
        # Residual assert
        assert residual_diff == 0, \
            'Error in sample residuals between {} and {}, number of residual diff: {} of {}'.format(
                alabel, blabel, residual_diff, nsampled_coordinates)


        # Compare analog

        analog_diff = nsampled_analog - np.sum(np.isclose(aanalog, banalog))
        assert analog_diff == 0, \
            'Mismatched analog samples between {} and {}, number of sampled diff: {} of {}'.format(
                alabel, blabel, analog_diff, nsampled_analog)
