''' Classes used to represent the concept of parameter groups in a .c3d file.
'''
import struct
import numpy as np
from .parameter import ParamData, Param
from .utils import Decorator


class GroupData(object):
    '''A group of parameters stored in a C3D file.

    In C3D files, parameters are organized in groups. Each group has a name (key), a
    description, and a set of named parameters. Each group is also internally associated
    with a numeric key.

    Attributes
    ----------
    dtypes : `c3d.dtypes.DataTypes`
        Data types object used for parsing.
    name : str
        Name of this parameter group.
    desc : str
        Description for this parameter group.
    '''

    def __init__(self, dtypes, name=None, desc=None):
        self._params = {}
        self._dtypes = dtypes
        # Assign through property setters
        self.set_name(name)
        self.set_desc(desc)

    def __repr__(self):
        return '<Group: {}>'.format(self.desc)

    def __contains__(self, key):
        return key in self._params

    def __getitem__(self, key):
        return self._params[key]

    @property
    def binary_size(self) -> int:
        '''Return the number of bytes to store this group and its parameters.'''
        return (
            1 +  # group_id
            1 + len(self.name.encode('utf-8')) +  # size of name and name bytes
            2 +  # next offset marker
            1 + len(self.desc.encode('utf-8')) +  # size of desc and desc bytes
            sum(p.binary_size for p in self._params.values()))

    def set_name(self, name):
        ''' Set the group name string. '''
        if name is None or isinstance(name, str):
            self.name = name
        else:
            raise TypeError('Expected group name to be string, was %s.' % type(name))

    def set_desc(self, desc):
        ''' Set the Group descriptor.
        '''
        if isinstance(desc, bytes):
            self.desc = self._dtypes.decode_string(desc)
        elif isinstance(desc, str) or desc is None:
            self.desc = desc
        else:
            raise TypeError('Expected descriptor to be python string, bytes or None, was %s.' % type(desc))

    def add_param(self, name, **kwargs):
        '''Add a parameter to this group.

        Parameters
        ----------
        name : str
            Name of the parameter to add to this group. The name will
            automatically be case-normalized.

        See constructor of `c3d.parameter.ParamData` for additional keyword arguments.

        Raises
        ------
        TypeError
            Input arguments are of the wrong type.
        KeyError
            Name or numerical key already exist (attempt to overwrite existing data).
        '''
        if not isinstance(name, str):
            raise TypeError("Expected 'name' argument to be a string, was of type {}".format(type(name)))
        name = name.upper()
        if name in self._params:
            raise KeyError('Parameter already exists with key {}'.format(name))
        self._params[name] = Param(ParamData(name, self._dtypes, **kwargs))

    def remove_param(self, name):
        '''Remove the specified parameter.

        Parameters
        ----------
        name : str
            Name for the parameter to remove.
        '''
        del self._params[name]

    def rename_param(self, name, new_name):
        ''' Rename a specified parameter group.

        Parameters
        ----------
        name : str, or `c3d.group.GroupReadonly`
            Parameter instance, or name.
        new_name : str
            New name for the parameter.
        Raises
        ------
        KeyError
            If no parameter with the original name exists.
        ValueError
            If the new name already exist (attempt to overwrite existing data).
        '''
        if new_name in self._params:
            raise ValueError("Key {} already exist.".format(new_name))
        if isinstance(name, Param):
            param = name
            name = param.name
        else:
            # Aquire instance using id
            param = self._params[name]
        del self._params[name]
        self._params[new_name] = param

    def write(self, group_id, handle):
        '''Write this parameter group, with parameters, to a file handle.

        Parameters
        ----------
        group_id : int
            The numerical ID of the group.
        handle : file handle
            An open, writable, binary file handle.
        '''
        name = self.name.encode('utf-8')
        desc = self.desc.encode('utf-8')
        handle.write(struct.pack('bb', len(name), -group_id))
        handle.write(name)
        handle.write(struct.pack('<h', 3 + len(desc)))
        handle.write(struct.pack('B', len(desc)))
        handle.write(desc)
        for param in self._params.values():
            param._data.write(group_id, handle)


class GroupReadonly(object):
    ''' Wrapper exposing readonly attributes of a `c3d.group.GroupData` entry.
    '''
    def __init__(self, data):
        self._data = data

    def __contains__(self, key):
        return key in self._data._params

    def __eq__(self, other):
        return self._data is other._data

    @property
    def name(self) -> str:
        ''' Access group name. '''
        return self._data.name

    @property
    def desc(self) -> str:
        '''Access group descriptor. '''
        return self._data.desc

    def items(self):
        ''' Get iterator for paramater key-entry pairs. '''
        return ((k, v.readonly()) for k, v in self._data._params.items())

    def values(self):
        ''' Get iterator for parameter entries. '''
        return (v.readonly() for v in self._data._params.values())

    def keys(self):
        ''' Get iterator for parameter entry keys. '''
        return self._data._params.keys()

    def get(self, key, default=None):
        '''Get a readonly parameter by key.

        Parameters
        ----------
        key : any
            Parameter key to look up in this group.
        default : any, optional
            Value to return if the key is not found. Defaults to None.

        Returns
        -------
        param : :class:`ParamReadable`
            A parameter from the current group.
        '''
        val = self._data._params.get(key, default)
        if val:
            return val.readonly()
        return default

    def get_int8(self, key):
        '''Get the value of the given parameter as an 8-bit signed integer.'''
        return self._data[key.upper()].int8_value

    def get_uint8(self, key):
        '''Get the value of the given parameter as an 8-bit unsigned integer.'''
        return self._data[key.upper()].uint8_value

    def get_int16(self, key):
        '''Get the value of the given parameter as a 16-bit signed integer.'''
        return self._data[key.upper()].int16_value

    def get_uint16(self, key):
        '''Get the value of the given parameter as a 16-bit unsigned integer.'''
        return self._data[key.upper()].uint16_value

    def get_int32(self, key):
        '''Get the value of the given parameter as a 32-bit signed integer.'''
        return self._data[key.upper()].int32_value

    def get_uint32(self, key):
        '''Get the value of the given parameter as a 32-bit unsigned integer.'''
        return self._data[key.upper()].uint32_value

    def get_float(self, key):
        '''Get the value of the given parameter as a 32-bit float.'''
        return self._data[key.upper()].float_value

    def get_bytes(self, key):
        '''Get the value of the given parameter as a byte array.'''
        return self._data[key.upper()].bytes_value

    def get_string(self, key):
        '''Get the value of the given parameter as a string.'''
        return self._data[key.upper()].string_value


class Group(GroupReadonly):
    ''' Wrapper exposing readable and writeable attributes of a `c3d.group.GroupData` entry.
    '''
    def __init__(self, data):
        super(Group, self).__init__(data)

    def readonly(self):
        ''' Returns a `c3d.group.GroupReadonly` instance with readonly access. '''
        return GroupReadonly(self._data)

    @property
    def name(self) -> str:
        ''' Get or set name. '''
        return self._data.name

    @name.setter
    def name(self, value) -> str:
        self._data.set_name(value)

    @property
    def desc(self) -> str:
        ''' Get or set descriptor. '''
        return self._data.desc

    @desc.setter
    def desc(self, value) -> str:
        self._data.set_desc(value)

    def items(self):
        ''' Iterator for paramater key-entry pairs. '''
        return ((k, v) for k, v in self._data._params.items())

    def values(self):
        ''' Iterator iterator for parameter entries. '''
        return (v for v in self._data._params.values())

    def get(self, key, default=None):
        '''Get a parameter by key.

        Parameters
        ----------
        key : any
            Parameter key to look up in this group.
        default : any, optional
            Value to return if the key is not found. Defaults to None.

        Returns
        -------
        param : :class:`ParamReadable`
            A parameter from the current group.
        '''
        return self._data._params.get(key, default)

    #
    #  Forward param editing
    #
    def add_param(self, name, **kwargs):
        '''Add a parameter to this group.

        See constructor of `c3d.parameter.ParamData` for additional keyword arguments.
        '''
        self._data.add_param(name, **kwargs)

    def remove_param(self, name):
        '''Remove the specified parameter.

        Parameters
        ----------
        name : str
            Name for the parameter to remove.
        '''
        self._data.remove_param(name)

    def rename_param(self, name, new_name):
        ''' Rename a specified parameter group.

        Parameters
        ----------
        See arguments in `c3d.group.GroupData.rename_param`.
        '''
        self._data.rename_param(name, new_name)

    #
    #   Convenience functions for adding parameters.
    #
    def add(self, name, desc, bpe, format, data, *dimensions):
        ''' Add a parameter with `data` package formated in accordance with `format`.

        Convenience function for `c3d.group.GroupData.add_param` calling struct.pack() on `data`.

        Example:

        >>> group.set('RATE', 'Point data sample rate', 4, '<f', 100)

        Parameters
        ----------
        name : str
            Parameter name.
        desc : str
            Parameter descriptor.
        bpe : int
            Number of bytes for each atomic element.
        format : str or None
            `struct.format()` compatible format string see:
            https://docs.python.org/3/library/struct.html#format-characters
        *dimensions : int, optional
            Shape associated with the data (if the data argument represents multiple elements).
        '''
        if isinstance(data, bytes):
            pass
        else:
            data = struct.pack(format, data)

        self.add_param(name,
                       desc=desc,
                       bytes_per_element=bpe,
                       bytes=data,
                       dimensions=list(dimensions))

    def add_array(self, name, desc, data, dtype=None):
        '''Add a parameter with the `data` package.

        Parameters
        ----------
        name : str
            Parameter name.
        desc : str
            Parameter descriptor.
        data : np.ndarray, or iterable
            Data array to encode in the parameter.
        dtype : np.dtype, optional
            Numpy data type used to encode the array (optional only if `data.dtype` returns a numpy type).
        '''
        if not isinstance(data, np.ndarray):
            if dtype is None:
                dtype = data.dtype
            data = np.array(data, dtype=dtype)
        elif dtype is None:
            dtype = data.dtype

        self.add_param(name,
                       desc=desc,
                       bytes_per_element=dtype.itemsize,
                       bytes=data.tobytes(),
                       dimensions=data.shape[::-1])

    def add_str(self, name, desc, data, *dimensions):
        ''' Add a string parameter.

        Parameters
        ----------
        name : str
            Parameter name.
        desc : str
            Parameter descriptor.
        data : str
            String to encode in the parameter.
        *dimensions : int, optional
            Shape associated with the string (if the string represents multiple elements).
        '''
        shape = list(dimensions)
        self.add_param(name,
                       desc=desc,
                       bytes_per_element=-1,
                       bytes=data.encode('utf-8'),
                       dimensions=shape or [len(data)])

    def add_empty_array(self, name, desc=''):
        ''' Add an empty parameter block.

        Parameters
        ----------
        name : str
            Parameter name.
        '''
        self.add_param(name, desc=desc,
                       bytes_per_element=0, dimensions=[0])

    #
    #   Convenience functions for adding or overwriting parameters.
    #
    def set(self, name, *args, **kwargs):
        ''' Add or overwrite a parameter with 'bytes' package formated in accordance with 'format'.

        See arguments in `c3d.group.Group.add`.
        '''
        try:
            self.remove_param(name)
        except KeyError as e:
            pass
        self.add(name, *args, **kwargs)

    def set_str(self, name, *args, **kwargs):
        ''' Add or overwrite a string parameter.

        See arguments in `c3d.group.Group.add_str`.
        '''
        try:
            self.remove_param(name)
        except KeyError as e:
            pass
        self.add_str(name, *args, **kwargs)

    def set_array(self, name, *args, **kwargs):
        ''' Add or overwrite a parameter with the `data` package.

        See arguments in `c3d.group.Group.add_array`.
        '''
        try:
            self.remove_param(name)
        except KeyError as e:
            pass
        self.add_array(name, *args, **kwargs)

    def set_empty_array(self, name, *args, **kwargs):
        ''' Add an empty parameter block.

        See arguments in `c3d.group.Group.add_empty_array`.
        '''
        try:
            self.remove_param(name)
        except KeyError as e:
            pass
        self.add_empty_array(name, *args, **kwargs)
