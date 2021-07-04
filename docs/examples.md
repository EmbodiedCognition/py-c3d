

Examples
========

Reading
-------

To read the frames from a C3D file, use a `c3d.reader.Reader` instance:

>>> import c3d
>>>
>>> reader = c3d.Reader(open('my-motion.c3d', 'rb'))
>>> for i, points, analog in reader.read_frames():
>>>     print('frame {}: point {}, analog {}'.format(
>>>           i, points.shape, analog.shape)

The method `c3d.reader.Reader.read_frames` generates tuples
containing the trial frame index, a ``numpy`` array of point data,
and a ``numpy`` array of analog data.

Writing
-------

To write data frames to a C3D file, use a `c3d.writer.Writer`
instance:

    import c3d
    import numpy as np

    # Writes 100 frames recorded at 200 Hz.
    # Each frame contains recordings for 24 coordinate markers.
    writer = c3d.Writer(point_rate=200)
    for _ in range(100):
        writer.add_frames((np.random.randn(24, 5), ()))

    writer.set_point_labels(['RFT1', 'RFT2', 'RFT3', 'RFT4',
                             'LFT1', 'LFT2', 'LFT3', 'LFT4',
                             'RSK1', 'RSK2', 'RSK3', 'RSK4',
                             'LSK1', 'LSK2', 'LSK3', 'LSK4',
                             'RTH1', 'RTH2', 'RTH3', 'RTH4',
                             'LTH1', 'LTH2', 'LTH3', 'LTH4'
                            ])
    writer.set_analog_labels(None)

    with open('random-points.c3d', 'wb') as h:
        writer.write(h)

The function `c3d.writer.Writer.add_frames` take pairs of ``numpy``
or python arrays. First array in each frame tuple contains the point
data and the second analog data for the frame. References of the data
are tracked until `c3d.writer.Writer.write` is called, serializing all
data frames to a C3D binary file.

Editing
-------
