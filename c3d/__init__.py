"""
=====================
Python C3D Processing
=====================

This package provides a single Python module for reading and writing binary
motion-capture files in the [C3D file format].

[C3D file format]: https://www.c3d.org/HTML/default.htm

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
