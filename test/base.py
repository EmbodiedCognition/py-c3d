import unittest
import numpy as np
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

        assert aheader.label_block == bheader.label_block, \
            '{}, label_block: {} {}, {} {}'.format(test_label,
            alabel, aheader.label_block, blabel, bheader.label_block)
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


    def compare_data(areader, breader):
        ''' Ensure data in reader a & b are equivalent.
        '''

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

        # Fetch file params/data
        frame_count = areader.frame_count
        analog_count = areader.analog_sample_count
        apoint, aanalog = Base.load_data(areader)
        bpoint, banalog = Base.load_data(breader)

        nsampled_coordinates = areader.point_used * areader.frame_count

        # Compare point data
        cam_index_diff = nsampled_coordinates - np.sum(np.isclose(apoint[:, 3], bpoint[:, 3]))
        assert cam_index_diff == 0, \
            'Error in camera index arrays, number of point diff: {} of {}'.format(cam_index_diff, nsampled_coordinates)
