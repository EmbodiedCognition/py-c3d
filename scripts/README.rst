Scripts are installed with the package and can be executed from a suitable command prompt by::

    script-name.py 'path-to-c3d-file'

or from the script directory::

    py .\script-name.py 'path-to-c3d-file' -options
    
The first option only works on Windows if .py files are associated with the python executable (`this answer`_ might help if its not working).

.. _this answer: https://stackoverflow.com/questions/1934675/how-to-execute-python-scripts-in-windows


CSV converter
~~~~~

Generate a .csv file from frame data contained in a .c3d file.

Invoke as::

    c3d2csv.py 'path-to-c3d-file' -options

Commandline options ::

    -r : Output column with residual values after point x,y,z coordinate columns.
    -c : Output column with camera counts as the last point coordinate column.
    -a : Output analog channel values after point coordinates.
    -e <end-line> : Endline string appended after each record (defaults to '\n').
    -s <separator> : Separator string inserted between records (defaults to ',').


NPZ converter
~~~~~

Generate a .npz file from frame data (point and analog) contained in a .c3d file.

Invoke as::

    c3d2npz.py 'path-to-c3d-file'

C3D Viewer
~~~~~

Simple 3D-viewer for displaying .c3d data.

Requirements ::

    pip install pyglet

Invoke  as::

    c3d-viewer.py 'path-to-c3d-file'

Interaction commands ::

    Esc :   Terminate
    Space : Pause
    Mouse : Orientate view

Metadata viewer
~~~~~

Prints metadata for a .c3d file to console.

Invoke as::

    c3d-metadata.py 'path-to-c3d-file'
