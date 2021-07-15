Examples
========

Access to data blocks in a .c3d file is provided through the `c3d.reader.Reader` and `c3d.writer.Writer` classes.
Implementation of the examples below are provided in the [examples/] directory in the github repository.

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
analog data for the frame. Leaving one of the arrays empty indicates
to the writer that no analog --- or point data--- should be included in the file.
References of the data arrays are tracked until `c3d.writer.Writer.write`
is called, which serializes the metadata and data frames into a C3D binary file stream.

Editing
-------

Editing c3d files is possible by combining the use of `c3d.reader.Reader` and `c3d.writer.Writer`
instances through the `c3d.reader.Reader.to_writer` method. To edit a file, open a file stream and pass
it to the `c3d.reader.Reader` constructor. Use the `c3d.reader.Reader.to_writer` method to create
an independent `c3d.writer.Writer` instance containing a heap copy of its file contents.
To edit the sequence, one can now reread the data frames from the reader and through inserting the
frames in reverse to create a looped version of the original motion sequence!

    import c3d

    with open('my-motion.c3d', 'rb') as file:
        reader = c3d.Reader(file)
        writer = reader.to_writer('copy')
        for i, points, analog in reader.read_frames():
            writer.add_frames((points, analog), index=reader.frame_count)

    with open('my-looped-motion.c3d', 'wb') as h:
        writer.write(h)


Accessing metadata
----------------

Metadata in a .c3d file exists in two forms, a `c3d.header.Header` and `c3d.parameter.ParamData`.
Reading metadata fields can be done though the `c3d.reader.Reader` but editing requires a
`c3d.writer.Writer` instance.

`c3d.header.Header` fields can be accessed from the common `c3d.manager.Manager.header` attribute.
Parameters are available through a parameter `c3d.group.Group`, and can be accessed
through the `c3d.manager.Manager.get` and `c3d.group.Group.get` methods:

    group = reader.get('POINT')
    param = group.get('LABELS')

or simply use

    param = reader.get('POINT:LABELS')

Note that for accessing parameters in the `c3d.reader.Reader`, `c3d.reader.Reader.get`
returns a `c3d.group.GroupReadonly` instance. Convenience functions are provided
for some of the common metadata fields such as `c3d.manager.Manager.frame_count`.
In the case you require specific metadata fields, consider exploring
the [C3D format manual] and/or inspect the file using the c3d-metadata script.

[C3D format manual]: https://c3d.org/docs/C3D_User_Guide.pdf

Writing metadata
----------------

Once a `c3d.writer.Writer` instance is created, to edit
parameter data `c3d.writer.Writer.get_create` a group:

    group = writer.get_create('ANALOG')

and to write a float32 entry, use the `c3d.group.Group.add` or `c3d.group.Group.set` functions

    group.set('GEN_SCALE', 'Analog general scale factor', 4, '<f', value)

In this case, one can use the `c3d.writer.Writer.set_analog_general_scale` method instead.
For serializing other types, see the source code for some of the convenience functions. For example:
`c3d.writer.Writer.set_point_labels` (2D string array) or
`c3d.writer.Writer.set_analog_scales` (1D float array).
