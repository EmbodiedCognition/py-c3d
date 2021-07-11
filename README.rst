py-c3d
======

This is a small library for reading and writing C3D binary files. C3D files are
a standard format for recording 3-dimensional time sequence data, especially
data recorded by a 3D motion tracking apparatus.

Installing
----------

Install with pip (currently outdated, download package from github instead)::

    pip install c3d

Or if you'd like to use the bleeding-edge version, just clone the github
repository and build and install using the normal Python setup process::

    git clone https://github.com/EmbodiedCognition/py-c3d
    cd py-c3d
    python setup.py install

Usage
-----

Documentation and examples are available in the `package documentation`_.

Tools
~~~~~

This package includes scripts_ for converting C3D motion data to CSV format
(``c3d2csv``) and an OpenGL-based visualization tool for observing the motion
described by a C3D file (``c3d-viewer``).

.. _scripts: ./scripts

Library
~~~~~~~

To use the C3D library, just import the package and create a ``Reader`` and/or
``Writer`` depending on your intended usage

.. code-block:: python

    import c3d

    with open('my-motion.c3d', 'rb') as file:
        reader = c3d.Reader(file)
        for i, points, analog in reader.read_frames():
            print('frame {}: point {}, analog {}'.format(
                  i, points.shape, analog.shape))

The librart also provide functionality for editing both frame and metadata fields; 
see the `package documentation`_ for more details.

.. _package documentation: https://mattiasfredriksson.github.io/py-c3d/c3d/

Caveats
-------

The package is tested against the available `software examples`_ but may still not support
every possible format. For example, parameters serialized in multiple parameters
are not handled automatically (such as a LABELS field stored in both POINT:LABELS and
POINT:LABELS2). Reading and writing files from a big-endian system is also not supported.

Tests are currently only run on Windows, which means that Linux and Mac users may
experience some issues. If you experience issues with a file or feature, feel free
to post an issue (preferably by including example file/code/python exception)
or make a pull request!

The package is Python only, support for other languages is available in other packages, for example see `ezc3d`_.

.. _software examples: https://www.c3d.org/sampledata.html
.. _ezc3d: https://github.com/pyomeca/ezc3d
