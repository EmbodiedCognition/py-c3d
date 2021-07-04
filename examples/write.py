import numpy as np
try:
    import c3d
except ModuleNotFoundError:
    # Force load package with no instalation
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..\\'))
    import c3d

# Writes 100 frames recorded at 200 Hz.
# Each frame contains recordings for 24 coordinate markers.
writer = c3d.Writer(point_rate=200)
for _ in range(100):
    writer.add_frames((np.random.randn(24, 5), ()))

writer.set_point_labels(['RFT1', 'RFT2', 'RFT3', 'RFT4', 'LFT1', 'LFT2', 'LFT3', 'LFT4',
                         'RSK1', 'RSK2', 'RSK3', 'RSK4', 'LSK1', 'LSK2', 'LSK3', 'LSK4',
                         'RTH1', 'RTH2', 'RTH3', 'RTH4', 'LTH1', 'LTH2', 'LTH3', 'LTH4'
                        ])
writer.set_analog_labels(None)

with open('random-points.c3d', 'wb') as h:
    writer.write(h)
