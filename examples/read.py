import numpy as np
import os
try:
    import c3d
except ModuleNotFoundError:
    # Force load package with no instalation
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..\\'))
    import c3d

# My motion == Sample01.Eb015pi.c3d
file_path = os.path.join(os.path.dirname(__file__), 'my-motion.c3d')

with open(file_path, 'rb') as file:
    reader = c3d.Reader(file)
    for i, points, analog in reader.read_frames():
        print('frame {}: point {}, analog {}'.format(
              i, points.shape, analog.shape))
