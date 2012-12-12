# py-c3d

This is a small library for reading and writing C3D binary files. C3D files are
a standard format for recording 3-dimensional time sequence data, especially
data recorded by a 3D motion tracking apparatus.

## Installing

Build and install using the normal Python distutils goodness :

    python setup.py build
    python setup.py install

If you just want to use the library, install with pip :

    pip install lmj.c3d

## Tools

This package includes a basic test for the library (`c3d_test.py`) and an
OpenGL-based visualization tool for watching C3D files (`c3d_viewer.py`).

## Caveats

This library is minimally effective, in the sense that the only motion tracking
system I have access to (for testing) is a Phasespace system. If you try out the
library and find that it doesn't work with your motion tracking system, let me
know.

Also, if you're looking for more functionality than just reading and writing C3D
files, there are a lot of better toolkits out there that support a lot more file
formats and provide more functionality. The [biomechanical toolkit][] is a good
example.

[biomechanical toolkit]: http://code.google.com/p/b-tk/
