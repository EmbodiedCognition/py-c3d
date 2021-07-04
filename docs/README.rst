Reading the docs
-----------------

Documentation is available at: https://mattiasfredriksson.github.io/py-c3d/c3d/

Building the docs
-----------------


Building the docs requires the pdoc3 package::

    pip install pdoc3

Once installed, documentation can be updated from the root directory with the command::

    pdoc --html c3d --force --config show_source_code=False  --output-dir docs

Once updated you can access the documentation in the `docs/c3d/`_ folder.

.. _docs/c3d/: docs/c3d/index.html 
