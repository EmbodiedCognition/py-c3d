Building the docs
-----------------


Requirement for building the documentation is the pdoc3 package::

    pip install pdoc3

and once installed the package can be built from the root directory with the command::

    pdoc --html c3d --force --config show_source_code=False  --output-dir docs
