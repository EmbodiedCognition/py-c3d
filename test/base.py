import unittest
import numpy as np
from test.zipload import Zipload

VERBOSE = False

class Base(unittest.TestCase):
    def setUp(self):
        Zipload.download()

    def _log(self, r):
        # Reduce test verbosity:
        if not VERBOSE:
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
