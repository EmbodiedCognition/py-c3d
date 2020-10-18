import unittest
import numpy as np
import warnings
import test.verify as verify
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
                        value = [s for s in p.string_array]
                    else:
                        value = p.string_value
                print(fmt.format(g, p, value))

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
        point_frames = np.zeros([nframe, npoint, 5], dtype=np.float64)
        analog_frames = np.zeros([nanalog_count, nanalog_channel], dtype=np.float64)

        # Start reading POINT and ANALOG blocks
        for i, points, analog in reader.read_frames(copy=False):
            # Extract columns 0:5
            index = i - first_frame
            aindex = index * nanalog_per_frame_samples
            point_frames[index] = points
            analog_frames[aindex:aindex+nanalog_per_frame_samples] = analog.T



        # Return data frames
        return point_frames, analog_frames


    def create_camera_mask(point_frames):
        ''' Create a mask for POINT data using the 4:th column.
        '''
        return point_frames[:, :, 4] >= 0


    def data_is_equal(areader, breader, alabel, blabel):
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

        nsampled_coordinates = areader.point_used * areader.frame_count
        nsampled_analog = areader.analog_used * analog_count

        # Compare point data (coordinates)
        c = ['X', 'Y', 'Z']
        for i in range(3):
            axis_diff = nsampled_coordinates - np.sum(np.isclose(apoint[:, :, i], bpoint[:, :, i],
                atol=equal_scale_fac*abs(areader.point_scale)))
            assert axis_diff == 0, \
                'Mismatched coordinates on {} axis for {} and {}, number of sampled diff: {} of {}'.format(
                c[i], alabel, blabel, axis_diff, nsampled_coordinates)

        # Word 4 (residual + camera bits)
        residual_diff = nsampled_coordinates - np.sum(np.isclose(apoint[:, :, 3], bpoint[:, :, 3]))
        cam_diff = nsampled_coordinates - np.sum(np.isclose(apoint[:, :, 4], bpoint[:, :, 4], atol=1.001))
        cam_diff_non_equal = nsampled_coordinates - np.sum(np.isclose(apoint[:, :, 4], bpoint[:, :, 4]))

        # Camera bit errors (warn if non identical, allow 1 cam bit diff, might be bad DEC implementation, or bad data)
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


    def check_data_in_range(reader, label, min_range, max_range):
        point, analog = Base.load_data(reader)
        # Probably redundant but can be useful to verify
        verify.array_match_headers(point, analog, reader, label)
        # Check POINT data blocks
        if reader.point_used > 0:
            point_masked = point[Base.create_camera_mask(point)]
            verify.point_data_in_range(point_masked, label, min_range, max_range)
        # Check ANALOG data blocks
        if reader.analog_used > 0:
            verify.analog_data_in_range(analog, label, min_range, max_range)
