Scripts
========

The package installation comes with some pre-packaged scripts for
viewing, and converting .c3d files to .csv and .npz formats.
See the [scripts/] directory on github for more information.

[scripts/]: https://github.com/EmbodiedCognition/py-c3d/tree/master/scripts

Examples
========

Access to data blocks in a .c3d file is provided through the `c3d.reader.Reader` and `c3d.writer.Writer` classes.
Runnable implementation of the examples are provided in the [examples/] directory in the github repository.

[examples/]: https://github.com/EmbodiedCognition/py-c3d/tree/master/examples

Reading
-------

To read the frames from a C3D file, use a `c3d.reader.Reader` instance:

    import c3d

    with open('my-motion.c3d', 'rb') as file:
        reader = c3d.Reader(file)
        for i, points, analog in reader.read_frames():
            print('frame {}: point {}, analog {}'.format(
                  i, points.shape, analog.shape))

The method `c3d.reader.Reader.read_frames` generates tuples
containing the trial frame number, a ``numpy`` array of point
data, and a ``numpy`` array of analog data.

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

The function `c3d.writer.Writer.add_frames` take pairs of ``numpy`` or ``python
arrays``, with the first array in each tuple defining point data and the second
defining the analog data for the frame. Leaving one of the arrays empty indicates
to the writer that no analog --- or point data--- should be included in the file.
References of the data arrays are tracked until `c3d.writer.Writer.write`
is called, which serializes metadata and data frames into a C3D binary file stream.

Editing
-------

Editing c3d files is possible by combining the use of `c3d.reader.Reader` and `c3d.writer.Writer`
instances through the use of `c3d.reader.Reader.to_writer`. By opening a .c3d file stream through
a reader instance, `c3d.reader.Reader.to_writer` can be used to create an independent Writer instance
copying the file contents onto the heap. Rereading the `reader` frame data from the file
and inserting the frames in reverse, a looped version of the .c3d file can be created!

    import c3d

    with open('my-motion.c3d', 'rb') as file:
        reader = c3d.Reader(file)
        writer = reader.to_writer('copy')
        for i, points, analog in reader.read_frames():
            writer.add_frames((points, analog), index=reader.frame_count)

    with open('my-looped-motion.c3d', 'wb') as h:
        writer.write(h)
