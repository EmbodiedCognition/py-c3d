Code style
----------

Use pycodestyle with the settings

    pycodestyle . --max-line-length 120

Pycodestyle can be installed with the pip command

    pip install pycodestyle

Docstrings
-----------

Use [numpy style] doc strings

[numpy style] https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard

Docstring example
-----------

    def my_function(aparam, bparam):
        ''' Short summary.

        Description, classes can be referred to through package/module `c3d.reader.Reader`.
        Methods can be referred to in the same way e.g. `c3d.reader.Reader.read_frames`.

        Parameters
        ----------
        aparam : `c3d.reader.Reader`
            This is the first input parameter.
        bparam : str
            The second parameter should be a string.

        Returns
        -------
        aarg : `c3d.writer.Writer`
            First return argument is a Writer instance.
        barg : int
            Second return argument is of type int.

        Raises
        ------
        ValueError
            It occurs for some reason.
        '''

        ...
        some_code
        ...

        return aarg, barg
