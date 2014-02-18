==========
Quickstart
==========

This is a small library for reading and writing C3D binary files. C3D files are
a standard format for recording 3-dimensional time sequence data, especially
data recorded by a 3D motion tracking apparatus.

Installing
----------

Install with pip::

    pip install c3d

Or if you'd like to use the bleeding-edge version, just clone the github
repository and build and install using the normal Python setup process::

    git clone https://github.com/EmbodiedCognition/py-c3d
    cd py-c3d
    python setup.py install

Usage
-----

Tools
~~~~~

This package includes a script for converting C3D motion data to CSV format
(``c3d2csv``) and an OpenGL-based visualization tool for observing the motion
described by a C3D file (``c3d-viewer``).

Library
~~~~~~~

To use the C3D library, just import the package and create a :class:`c3d.Reader`
or :class:`c3d.Writer` depending on your intended usage::

    import c3d

    with open('data.c3d', 'rb') as handle:
        reader = :class:`c3d.Reader`(handle)
        for i, (points, analog) in enumerate(reader.read_frames()):
            print('Frame {}: {}'.format(i, points.round(2)))

You can also get and set metadata fields using the library; see the `package
documentation`_ for more details.

.. _package documentation: http://c3d.readthedocs.org
