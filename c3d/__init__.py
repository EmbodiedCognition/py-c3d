"""
---------------------
Python C3D Processing
---------------------

This package provides pure Python modules for reading, writing, and editing binary
motion-capture files in the [C3D file format].

[C3D file format]: https://www.c3d.org/HTML/default.htm

Installing
----------

See the [main page] or [github page].

[main page]: https://mattiasfredriksson.github.io/py-c3d/
[github page]: https://github.com/EmbodiedCognition/py-c3d

.. include:: ../docs/examples.md

"""
from . import dtypes
from . import group
from . import header
from . import manager
from . import parameter
from . import utils
from .reader import Reader
from .writer import Writer
