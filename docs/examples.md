

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

>>> import c3d
>>> import numpy as np
>>>
>>> writer = c3d.Writer()
>>> for _ in range(100):
>>>     writer.add_frame(np.random.randn(30, 5))
>>> with open('random-points.c3d', 'wb') as h:
>>>     writer.write(h)

The function `c3d.writer.Writer.add_frames` takes ``numpy`` array of
point data---and, optionally, a ``numpy`` array of analog data---and adds it to
an internal data buffer. The function `c3d.writer.Writer.write` serializes
all of the frame data to a C3D binary file.

Editing
-------
