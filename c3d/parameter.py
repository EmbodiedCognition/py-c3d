''' Classes used to represent the concept of a parameter in a .c3d file.
'''
import struct
import numpy as np
from .utils import DEC_to_IEEE, DEC_to_IEEE_BYTES


class ParamData(object):
    '''A class representing a single named parameter from a C3D file.

    Attributes
    ----------
    name : str
        Name of this parameter.
    dtype: DataTypes
        Reference to the DataTypes object associated with the file.
    desc : str
        Brief description of this parameter.
    bytes_per_element : int, optional
        For array data, this describes the size of each element of data. For
        string data (including arrays of strings), this should be -1.
    dimensions : list of int
        For array data, this describes the dimensions of the array, stored in
        column-major (Fortran) order. For arrays of strings, the dimensions here will be
        the number of columns (length of each string) followed by the number of
        rows (number of strings).
    bytes : str
        Raw data for this parameter.
    '''

    def __init__(self,
                 name,
                 dtype,
                 desc='',
                 bytes_per_element=1,
                 dimensions=None,
                 bytes=b'',
                 handle=None):
        '''Set up a new parameter, only the name is required.'''
        self.name = name
        self.dtypes = dtype
        self.desc = desc
        self.bytes_per_element = bytes_per_element
        self.dimensions = dimensions or []
        self.bytes = bytes
        if handle:
            self.read(handle)

    def __repr__(self):
        return '<Param: {}>'.format(self.desc)

    @property
    def num_elements(self) -> int:
        '''Return the number of elements in this parameter's array value.'''
        e = 1
        for d in self.dimensions:
            e *= d
        return e

    @property
    def total_bytes(self) -> int:
        '''Return the number of bytes used for storing this parameter's data.'''
        return self.num_elements * abs(self.bytes_per_element)

    @property
    def binary_size(self) -> int:
        '''Return the number of bytes needed to store this parameter.'''
        return (
            1 +  # group_id
            2 +  # next offset marker
            1 + len(self.name.encode('utf-8')) +  # size of name and name bytes
            1 +  # data size
            # size of dimensions and dimension bytes
            1 + len(self.dimensions) +
            self.total_bytes +  # data
            1 + len(self.desc.encode('utf-8'))  # size of desc and desc bytes
        )

    def write(self, group_id, handle):
        '''Write binary data for this parameter to a file handle.

        Parameters
        ----------
        group_id : int
            The numerical ID of the group that holds this parameter.
        handle : file handle
            An open, writable, binary file handle.
        '''
        name = self.name.encode('utf-8')
        handle.write(struct.pack('bb', len(name), group_id))
        handle.write(name)
        handle.write(struct.pack('<h', self.binary_size - 2 - len(name)))
        handle.write(struct.pack('b', self.bytes_per_element))
        handle.write(struct.pack('B', len(self.dimensions)))
        handle.write(struct.pack('B' * len(self.dimensions), *self.dimensions))
        if self.bytes is not None and len(self.bytes) > 0:
            handle.write(self.bytes)
        desc = self.desc.encode('utf-8')
        handle.write(struct.pack('B', len(desc)))
        handle.write(desc)

    def read(self, handle):
        '''Read binary data for this parameter from a file handle.

        This reads exactly enough data from the current position in the file to
        initialize the parameter.
        '''
        self.bytes_per_element, = struct.unpack('b', handle.read(1))
        dims, = struct.unpack('B', handle.read(1))
        self.dimensions = [struct.unpack('B', handle.read(1))[
            0] for _ in range(dims)]
        self.bytes = b''
        if self.total_bytes:
            self.bytes = handle.read(self.total_bytes)
        desc_size, = struct.unpack('B', handle.read(1))
        self.desc = desc_size and self.dtypes.decode_string(handle.read(desc_size)) or ''

    def _as(self, dtype):
        '''Unpack the raw bytes of this param using the given struct format.'''
        return np.frombuffer(self.bytes, count=1, dtype=dtype)[0]

    def _as_array(self, dtype, copy=True):
        '''Unpack the raw bytes of this param using the given data format.'''
        if not self.dimensions:
            return [self._as(dtype)]
        elems = np.frombuffer(self.bytes, dtype=dtype)
        # Reverse shape as the shape is defined in fortran format
        view = elems.reshape(self.dimensions[::-1])
        if copy:
            return view.copy()
        return view


class ParamReadonly(object):
    ''' Wrapper exposing readonly attributes of a `c3d.parameter.ParamData` entry.
    '''

    def __init__(self, data):
        self._data = data

    def __eq__(self, other):
        return self._data is other._data

    @property
    def name(self) -> str:
        ''' Get the parameter name. '''
        return self._data.name

    @property
    def desc(self) -> str:
        ''' Get the parameter descriptor. '''
        return self._data.desc

    @property
    def dtypes(self):
        ''' Convenience accessor to the `c3d.dtypes.DataTypes` instance associated with the parameter. '''
        return self._data.dtypes

    @property
    def dimensions(self) -> (int, ...):
        ''' Shape of the parameter data (Fortran format). '''
        return self._data.dimensions

    @property
    def num_elements(self) -> int:
        '''Return the number of elements in this parameter's array value.'''
        return self._data.num_elements

    @property
    def bytes_per_element(self) -> int:
        '''Return the number of bytes used to store each data element.'''
        return self._data.bytes_per_element

    @property
    def total_bytes(self) -> int:
        '''Return the number of bytes used for storing this parameter's data.'''
        return self._data.total_bytes

    @property
    def binary_size(self) -> int:
        '''Return the number of bytes needed to store this parameter.'''
        return self._data.binary_size

    @property
    def int8_value(self):
        '''Get the parameter data as an 8-bit signed integer.'''
        return self._data._as(self.dtypes.int8)

    @property
    def uint8_value(self):
        '''Get the parameter data as an 8-bit unsigned integer.'''
        return self._data._as(self.dtypes.uint8)

    @property
    def int16_value(self):
        '''Get the parameter data as a 16-bit signed integer.'''
        return self._data._as(self.dtypes.int16)

    @property
    def uint16_value(self):
        '''Get the parameter data as a 16-bit unsigned integer.'''
        return self._data._as(self.dtypes.uint16)

    @property
    def int32_value(self):
        '''Get the parameter data as a 32-bit signed integer.'''
        return self._data._as(self.dtypes.int32)

    @property
    def uint32_value(self):
        '''Get the parameter data as a 32-bit unsigned integer.'''
        return self._data._as(self.dtypes.uint32)

    @property
    def uint_value(self):
        ''' Get the parameter data as a unsigned integer of appropriate type. '''
        if self.bytes_per_element >= 4:
            return self.uint32_value
        elif self.bytes_per_element >= 2:
            return self.uint16_value
        else:
            return self.uint8_value

    @property
    def int_value(self):
        ''' Get the parameter data as a signed integer of appropriate type. '''
        if self.bytes_per_element >= 4:
            return self.int32_value
        elif self.bytes_per_element >= 2:
            return self.int16_value
        else:
            return self.int8_value

    @property
    def float_value(self):
        '''Get the parameter data as a floating point value of appropriate type.'''
        if self.bytes_per_element > 4:
            if self.dtypes.is_dec:
                raise AttributeError("64 bit DEC floating point is not supported.")
            # 64-bit floating point is not a standard
            return self._data._as(self.dtypes.float64)
        elif self.bytes_per_element == 4:
            if self.dtypes.is_dec:
                return DEC_to_IEEE(self._data._as(np.uint32))
            else:  # is_mips or is_ieee
                return self._data._as(self.dtypes.float32)
        else:
            raise AttributeError("Only 32 and 64 bit floating point is supported.")

    @property
    def bytes_value(self) -> bytes:
        '''Get the raw byte string.'''
        return self._data.bytes

    @property
    def string_value(self):
        '''Get the parameter data as a unicode string.'''
        return self.dtypes.decode_string(self._data.bytes)

    @property
    def int8_array(self):
        '''Get the parameter data as an array of 8-bit signed integers.'''
        return self._data._as_array(self.dtypes.int8)

    @property
    def uint8_array(self):
        '''Get the parameter data as an array of 8-bit unsigned integers.'''
        return self._data._as_array(self.dtypes.uint8)

    @property
    def int16_array(self):
        '''Get the parameter data as an array of 16-bit signed integers.'''
        return self._data._as_array(self.dtypes.int16)

    @property
    def uint16_array(self):
        '''Get the parameter data as an array of 16-bit unsigned integers.'''
        return self._data._as_array(self.dtypes.uint16)

    @property
    def int32_array(self):
        '''Get the parameter data as an array of 32-bit signed integers.'''
        return self._data._as_array(self.dtypes.int32)

    @property
    def uint32_array(self):
        '''Get the parameter data as an array of 32-bit unsigned integers.'''
        return self._data._as_array(self.dtypes.uint32)

    @property
    def int64_array(self):
        '''Get the parameter data as an array of 32-bit signed integers.'''
        return self._data._as_array(self.dtypes.int64)

    @property
    def uint64_array(self):
        '''Get the parameter data as an array of 32-bit unsigned integers.'''
        return self._data._as_array(self.dtypes.uint64)

    @property
    def float32_array(self):
        '''Get the parameter data as an array of 32-bit floats.'''
        # Convert float data if not IEEE processor
        if self.dtypes.is_dec:
            # _as_array but for DEC
            if not self.dimensions:
                return [self.float_value]
            return DEC_to_IEEE_BYTES(self._data.bytes).reshape(self.dimensions[::-1])  # Reverse fortran format
        else:  # is_ieee or is_mips
            return self._data._as_array(self.dtypes.float32)

    @property
    def float64_array(self):
        '''Get the parameter data as an array of 64-bit floats.'''
        # Convert float data if not IEEE processor
        if self.dtypes.is_dec:
            raise ValueError('Unable to convert bytes encoded in a 64 bit floating point DEC format.')
        else:  # is_ieee or is_mips
            return self._data._as_array(self.dtypes.float64)

    @property
    def float_array(self):
        '''Get the parameter data as an array of 32 or 64 bit floats.'''
        # Convert float data if not IEEE processor
        if self.bytes_per_element == 4:
            return self.float32_array
        elif self.bytes_per_element == 8:
            return self.float64_array
        else:
            raise TypeError("Parsing parameter bytes to an array with %i bit " % self.bytes_per_element +
                            "floating-point precission is not unsupported.")

    @property
    def int_array(self):
        '''Get the parameter data as an array of integer values.'''
        # Convert float data if not IEEE processor
        if self.bytes_per_element == 1:
            return self.int8_array
        elif self.bytes_per_element == 2:
            return self.int16_array
        elif self.bytes_per_element == 4:
            return self.int32_array
        elif self.bytes_per_element == 8:
            return self.int64_array
        else:
            raise TypeError("Parsing parameter bytes to an array with %i bit integer values is not unsupported." %
                            self.bytes_per_element)

    @property
    def uint_array(self):
        '''Get the parameter data as an array of integer values.'''
        # Convert float data if not IEEE processor
        if self.bytes_per_element == 1:
            return self.uint8_array
        elif self.bytes_per_element == 2:
            return self.uint16_array
        elif self.bytes_per_element == 4:
            return self.uint32_array
        elif self.bytes_per_element == 8:
            return self.uint64_array
        else:
            raise TypeError("Parsing parameter bytes to an array with %i bit integer values is not unsupported." %
                            self.bytes_per_element)

    @property
    def bytes_array(self):
        '''Get the parameter data as an array of raw byte strings.'''
        # Decode different dimensions
        if len(self.dimensions) == 0:
            return np.array([])
        elif len(self.dimensions) == 1:
            return np.array(self._data.bytes)
        else:
            # Convert Fortran shape (data in memory is identical, shape is transposed)
            word_len = self.dimensions[0]
            dims = self.dimensions[1:][::-1]  # Identical to: [:0:-1]
            byte_steps = np.cumprod(self.dimensions[:-1])[::-1]
            # Generate mult-dimensional array and parse byte words
            byte_arr = np.empty(dims, dtype=object)
            for i in np.ndindex(*dims):
                # Calculate byte offset as sum of each array index times the byte step of each dimension.
                off = np.sum(np.multiply(i, byte_steps))
                byte_arr[i] = self._data.bytes[off:off+word_len]
            return byte_arr

    @property
    def string_array(self):
        '''Get the parameter data as a python array of unicode strings.'''
        # Decode different dimensions
        if len(self.dimensions) == 0:
            return np.array([])
        elif len(self.dimensions) == 1:
            return np.array([self.string_value])
        else:
            # Parse byte sequences
            byte_arr = self.bytes_array
            # Decode sequences
            for i in np.ndindex(byte_arr.shape):
                byte_arr[i] = self.dtypes.decode_string(byte_arr[i])
            return byte_arr

    @property
    def any_value(self):
        ''' Get the parameter data as a value of 'traditional type'.

        Traditional types are defined in the Parameter section in the [user manual].

        Returns
        -------
        value : int, float, or str
            Depending on the `bytes_per_element` field, a traditional type can
            be a either a signed byte, signed short, 32-bit float, or a string.

        [user manual]: https://www.c3d.org/docs/C3D_User_Guide.pdf
        '''
        if self.bytes_per_element >= 4:
            return self.float_value
        elif self.bytes_per_element >= 2:
            return self.int16_value
        elif self.bytes_per_element == -1:
            return self.string_value
        else:
            return self.int8_value

    @property
    def any_array(self):
        ''' Get the parameter data as an array of 'traditional type'.

        Traditional types are defined in the Parameter section in the [user manual].

        Returns
        -------
        value : array
            Depending on the `bytes_per_element` field, a traditional type can
            be a either a signed byte, signed short, 32-bit float, or a string.

        [user manual]: https://www.c3d.org/docs/C3D_User_Guide.pdf
        '''
        if self.bytes_per_element >= 4:
            return self.float_array
        elif self.bytes_per_element >= 2:
            return self.int16_array
        elif self.bytes_per_element == -1:
            return self.string_array
        else:
            return self.int8_array

    @property
    def _as_any_uint(self):
        ''' Attempt to parse the parameter data as any unsigned integer format.
            Checks if the integer is stored as a floating point value.

            Can be used to read 'POINT:FRAMES' or 'POINT:LONG_FRAMES'
            when not accessed through `c3d.manager.Manager.last_frame`.
        '''
        if self.bytes_per_element >= 4:
            # Check if float value representation is an integer
            value = self.float_value
            if float(value).is_integer():
                return int(value)
            return self.uint32_value
        elif self.bytes_per_element >= 2:
            return self.uint16_value
        else:
            return self.uint8_value


class Param(ParamReadonly):
    ''' Wrapper exposing both readable and writable attributes of a `c3d.parameter.ParamData` entry.
    '''
    def __init__(self, data):
        super(Param, self).__init__(data)

    def readonly(self):
        ''' Returns a readonly `c3d.parameter.ParamReadonly` instance. '''
        return ParamReadonly(self._data)

    @property
    def bytes(self) -> bytes:
        ''' Get or set the parameter bytes. '''
        return self._data.bytes

    @bytes.setter
    def bytes(self, value):
        self._data.bytes = value
