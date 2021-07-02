import struct
import numpy as np
from .parameter import ParamData, ParamReadonly, ParamWritable
from .utils import Decorator

class GroupData(object):
    '''A group of parameters from a C3D file.

    In C3D files, parameters are organized in groups. Each group has a name, a
    description, and a set of named parameters.

    Attributes
    ----------
    dtypes : 'DataTypes'
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
    def binary_size(self):
        '''Return the number of bytes to store this group and its parameters.'''
        return (
            1 +  # group_id
            1 + len(self.name.encode('utf-8')) +  # size of name and name bytes
            2 +  # next offset marker
            1 + len(self.desc.encode('utf-8')) +  # size of desc and desc bytes
            sum(p.binary_size for p in self._params.values()))

    def set_name(self, value):
        ''' Set the group name string. '''
        if value is None or isinstance(value, str):
            self.name = value
        else:
            raise TypeError('Expected group name to be string, was %s.' % type(value))

    def set_desc(self, value):
        ''' Set the Group descriptor.
        '''
        if isinstance(value, bytes):
            self.desc = self._dtypes.decode_string(value)
        elif isinstance(value, str) or value is None:
            self.desc = value
        else:
            raise TypeError('Expected descriptor to be python string, bytes or None, was %s.' % type(value))

    def add_param(self, name, **kwargs):
        '''Add a parameter to this group.

        Parameters
        ----------
        name : str
            Name of the parameter to add to this group. The name will
            automatically be case-normalized.

        Additional keyword arguments will be passed to the `ParamData` constructor.

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
        self._params[name] = ParamData(name, self._dtypes, **kwargs)

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
        name : str, or 'ParamData'
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
        if isinstance(name, ParamData):
            param = name
            name = param.name
        else:
            # Aquire instance using id
            param = self._params.get(name, None)
            if param is None:
                raise KeyError('No parameter found matching the identifier: {}'.format(str(name)))
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
            param.write(group_id, handle)

class GroupReadonly(object):
    ''' Handle exposing readable attributes of a GroupData entry.
    '''
    def __init__(self, data):
        self._data = data

    def __contains__(self, key):
        return key in self._data._params

    @property
    def name(self):
        ''' Group name. '''
        return self._data.name

    @property
    def desc(self):
        ''' Group descriptor. '''
        return self._data.desc

    def items(self):
        ''' Acquire iterator for paramater key-entry pairs. '''
        return ((k, ParamReadonly(v)) for k, v in self._data._params.items())

    def values(self):
        ''' Acquire iterator for parameter entries. '''
        return (ParamReadonly(v) for v in self._data._params.values())

    def keys(self):
        ''' Acquire iterator for parameter entry keys. '''
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
        val = self._data._params.get(key)
        if val:
            return ParamReadonly(val)
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

class GroupWritable(GroupReadonly):
    ''' Handle exposing readable and writeable attributes of a GroupData entry.

     Group instance decorator providing convenience functions for Writer editing.
    '''
    def __init__(self, data):
        super(GroupWritable, self).__init__(data)

    def readonly(self):
        ''' Make access readonly. '''
        return GroupReadonly(self._data)

    @property
    def name(self):
        ''' Group name. '''
        return self._data.name

    @name.setter
    def name(self, value):
        ''' Group name string.

        Parameters
        ----------
        value : str
            New name for the group.
        '''
        self._data.set_name(value)

    @property
    def desc(self):
        ''' Group descriptor. '''
        return self._data.desc

    @desc.setter
    def desc(self, value):
        ''' Group descriptor.

        Parameters
        ----------
        value : str, or bytes
            New description for this parameter group.
        '''
        self._data.set_desc(value)

    def items(self):
        ''' Acquire iterator for paramater key-entry pairs. '''
        return ((k, ParamWritable(v)) for k, v in self._data._params.items())

    def values(self):
        ''' Acquire iterator for parameter entries. '''
        return (ParamWritable(v) for v in self._data._params.values())

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
        val = self._data._params.get(key)
        if val:
            return ParamWritable(val)
        return default
    #
    #  Forward param editing
    #
    def add_param(self, name, **kwargs):
        '''Add a parameter to this group.

        Parameters
        ----------
        name : str
            Name of the parameter to add to this group. The name will
            automatically be case-normalized.

        Additional keyword arguments will be passed to the `ParamData` constructor.

        Raises
        ------
        TypeError
            Input arguments are of the wrong type.
        KeyError
            Name or numerical key already exist (attempt to overwrite existing data).
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
        name : str, or 'ParamData'
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
        self._data.rename_param(name, new_name)

    #
    #   Add decorator functions (throws on overwrite)
    #
    def add(self, name, desc, bpe, format, data, *dimensions):
        ''' Add a parameter with 'data' package formated in accordance with 'format'.
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
        '''Add a parameter with the 'data' package.

        Arguments
        ---------
        data : Numpy array, or python iterable.
        dtype : Numpy dtype to encode the array (Optional if data is numpy type).
        '''
        if not isinstance(data, np.ndarray):
            if dtype is not None:
                raise ValueError('Must specify dtype when passning non-numpy array type.')
            data = np.array(data, dtype=dtype)
        elif dtype is None:
            dtype = data.dtype

        self.add_param(name,
                       desc=desc,
                       bytes_per_element=dtype.itemsize,
                       bytes=data,
                       dimensions=data.shape)

    def add_str(self, name, desc, data, *dimensions):
        ''' Add a string parameter.
        '''
        self.add_param(name,
                       desc=desc,
                       bytes_per_element=-1,
                       bytes=data.encode('utf-8'),
                       dimensions=list(dimensions))

    def add_empty_array(self, name, desc, bpe):
        ''' Add an empty parameter block.
        '''
        self.add_param(name, desc=desc,
                       bytes_per_element=bpe, dimensions=[0])

    #
    #   Set decorator functions (overwrite)
    #
    def set(self, name, *args, **kwargs):
        ''' Add or overwrite a parameter with 'bytes' package formated in accordance with 'format'.
        '''
        try:
            self.remove_param(name)
        except KeyError as e:
            pass
        self.add(name, *args, **kwargs)

    def set_str(self, name, *args, **kwargs):
        ''' Add a string parameter.
        '''
        try:
            self.remove_param(name)
        except KeyError as e:
            pass
        self.add_str(name, *args, **kwargs)

    def set_array(self, name, *args, **kwargs):
        ''' Add a string parameter.
        '''
        try:
            self.remove_param(name)
        except KeyError as e:
            pass
        self.add_array(name, *args, **kwargs)

    def set_empty_array(self, name, *args, **kwargs):
        ''' Add an empty parameter block.
        '''
        try:
            self.remove_param(name)
        except KeyError as e:
            pass
        self.add_empty_array(name, *args, **kwargs)
