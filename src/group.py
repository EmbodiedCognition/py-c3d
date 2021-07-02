import struct
import numpy as np
from .parameter import Param

class Group(object):
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
        self.name = name
        self.desc = desc

    def __repr__(self):
        return '<Group: {}>'.format(self.desc)

    def __contains__(self, key):
        return key in self._params

    @property
    def name(self):
        ''' Group name. '''
        return self._name

    @name.setter
    def name(self, value):
        ''' Group name string.

        Parameters
        ----------
        value : str
            New name for the group.
        '''
        if value is None or isinstance(value, str):
            self._name = value
        else:
            raise TypeError('Expected group name to be string, was %s.' % type(value))

    @property
    def desc(self):
        ''' Group descriptor. '''
        return self._desc

    @desc.setter
    def desc(self, value):
        ''' Group descriptor.

        Parameters
        ----------
        value : str, or bytes
            New description for this parameter group.
        '''
        if isinstance(value, bytes):
            self._desc = self._dtypes.decode_string(value)
        elif isinstance(value, str) or value is None:
            self._desc = value
        else:
            raise TypeError('Expected descriptor to be python string, bytes or None, was %s.' % type(value))

    def param_items(self):
        ''' Acquire iterator for paramater key-entry pairs. '''
        return self._params.items()

    def param_values(self):
        ''' Acquire iterator for parameter entries. '''
        return self._params.values()

    def param_keys(self):
        ''' Acquire iterator for parameter entry keys. '''
        return self._params.keys()

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
        param : :class:`Param`
            A parameter from the current group.
        '''
        return self._params.get(key, default)

    def add_param(self, name, **kwargs):
        '''Add a parameter to this group.

        Parameters
        ----------
        name : str
            Name of the parameter to add to this group. The name will
            automatically be case-normalized.

        Additional keyword arguments will be passed to the `Param` constructor.

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
        self._params[name] = Param(name, self._dtypes, **kwargs)

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
        name : str, or 'Param'
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
            param = self._params.get(name, None)
            if param is None:
                raise KeyError('No parameter found matching the identifier: {}'.format(str(name)))
        del self._params[name]
        self._params[new_name] = param

    def binary_size(self):
        '''Return the number of bytes to store this group and its parameters.'''
        return (
            1 +  # group_id
            1 + len(self._name.encode('utf-8')) +  # size of name and name bytes
            2 +  # next offset marker
            1 + len(self._desc.encode('utf-8')) +  # size of desc and desc bytes
            sum(p.binary_size() for p in self._params.values()))

    def write(self, group_id, handle):
        '''Write this parameter group, with parameters, to a file handle.

        Parameters
        ----------
        group_id : int
            The numerical ID of the group.
        handle : file handle
            An open, writable, binary file handle.
        '''
        name = self._name.encode('utf-8')
        desc = self._desc.encode('utf-8')
        handle.write(struct.pack('bb', len(name), -group_id))
        handle.write(name)
        handle.write(struct.pack('<h', 3 + len(desc)))
        handle.write(struct.pack('B', len(desc)))
        handle.write(desc)
        for param in self._params.values():
            param.write(group_id, handle)

    def get_int8(self, key):
        '''Get the value of the given parameter as an 8-bit signed integer.'''
        return self._params[key.upper()].int8_value

    def get_uint8(self, key):
        '''Get the value of the given parameter as an 8-bit unsigned integer.'''
        return self._params[key.upper()].uint8_value

    def get_int16(self, key):
        '''Get the value of the given parameter as a 16-bit signed integer.'''
        return self._params[key.upper()].int16_value

    def get_uint16(self, key):
        '''Get the value of the given parameter as a 16-bit unsigned integer.'''
        return self._params[key.upper()].uint16_value

    def get_int32(self, key):
        '''Get the value of the given parameter as a 32-bit signed integer.'''
        return self._params[key.upper()].int32_value

    def get_uint32(self, key):
        '''Get the value of the given parameter as a 32-bit unsigned integer.'''
        return self._params[key.upper()].uint32_value

    def get_float(self, key):
        '''Get the value of the given parameter as a 32-bit float.'''
        return self._params[key.upper()].float_value

    def get_bytes(self, key):
        '''Get the value of the given parameter as a byte array.'''
        return self._params[key.upper()].bytes_value

    def get_string(self, key):
        '''Get the value of the given parameter as a string.'''
        return self._params[key.upper()].string_value
