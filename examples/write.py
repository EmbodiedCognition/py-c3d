import numpy as np
try:
    import c3d
except ModuleNotFoundError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..\\'))
    import c3d


writer = c3d.Writer()
for _ in range(100):
    writer.add_frames((np.random.randn(30, 5), ()))
writer.set_point_labels(['RFT1', 'RFT2', 'RFT3', 'LFT1', 'LFT2'])
writer.set_analog_labels(None)
with open('random-points.c3d', 'wb') as h:
    writer.write(h)
