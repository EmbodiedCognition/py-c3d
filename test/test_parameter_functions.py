import c3d
import struct
import unittest
import numpy as np


def genByteWordArr(word, shape):
    '''    Generate a multi-dimensional byte array from a specific word.
    '''
    arr = np.array(word)
    for d in shape[::-1]:
        arr = arr[np.newaxis].repeat(d, 0)
    return arr, [len(word)] + [d for d in shape]


def genRndByteArr(wordlen, shape, pad):
    '''    Generate a multi-dimensional byte array with random data.
    '''
    tot_len = wordlen + pad*wordlen
    arr = np.empty(shape, dtype=np.dtype('S'+str(tot_len)))
    for i in np.ndindex(arr.shape):
        bytes = np.random.randint(21, 126, wordlen).astype(np.uint8)
        if pad:
            bytes = np.hstack((bytes, np.array([b'255']*wordlen, dtype=np.uint8)))
        arr[i] = bytes.tobytes()
    return arr, [tot_len] + [d for d in shape]


def genRndFloatArr(shape, rnd, range=(-1e6, 1e6)):
    '''    Generate a multi-dimensional array of 32 bit floating point data.
    '''
    return rnd.uniform(range[0], range[1], shape)


class ParameterValueTest(unittest.TestCase):
    '''    Test read Parameter arrays
    '''

    RANGE_8_BIT = (-127, 127)
    RANGE_16_BIT = (-1e4, 1e4)
    RANGE_32_BIT = (-1e6, 1e6)
    RANGE_8_UNSIGNED_BIT = (0, 255)
    RANGE_16_UNSIGNED_BIT = (0, 1e4)
    RANGE_32_UNSIGNED_BIT = (0, 1e6)
    TEST_ITERATIONS = 1000

    def setUp(self):
        self.rnd = np.random.default_rng()
        self.dtypes = c3d.DataTypes(c3d.PROCESSOR_INTEL)

    def test_a_param_float32(self):
        '''    Verify a single 32 bit floating point value is parsed correctly
        '''
        for i in range(ParameterValueTest.TEST_ITERATIONS):
            value = np.float32(self.rnd.uniform(*ParameterValueTest.RANGE_32_BIT))
            bytes = struct.pack('<f', value)
            P = c3d.Param('FLOAT_TEST', self.dtypes, bytes_per_element=4, dimensions=[1], bytes=bytes)
            value_out = P.float_value
            assert value == value_out, 'Parameter float was not read correctly. Was %f, expected %f' %\
                (value_out, value)

    def test_b_param_int32(self):
        '''    Verify a single 32 bit integer value is parsed correctly
        '''
        for i in range(ParameterValueTest.TEST_ITERATIONS):
            value = np.int32(self.rnd.uniform(*ParameterValueTest.RANGE_32_BIT))
            bytes = struct.pack('<i', value)
            P = c3d.Param('INT32_TEST', self.dtypes, bytes_per_element=4, dimensions=[1], bytes=bytes)
            value_out = P.int32_value
            assert value == value_out, 'Parameter int32 was not read correctly. Was %f, expected %f' %\
                (value_out, value)

    def test_b_param_uint32(self):
        '''    Verify a single 32 bit unsigned integer value is parsed correctly
        '''
        for i in range(ParameterValueTest.TEST_ITERATIONS):
            value = np.uint32(self.rnd.uniform(*ParameterValueTest.RANGE_32_UNSIGNED_BIT))
            bytes = struct.pack('<I', value)
            P = c3d.Param('UINT32_TEST', self.dtypes, bytes_per_element=4, dimensions=[1], bytes=bytes)
            value_out = P.int32_value
            assert value == value_out, 'Parameter uint32 was not read correctly. Was %f, expected %f' %\
                (value_out, value)

    def test_b_param_int16(self):
        '''    Verify a single 16 bit integer value is parsed correctly
        '''
        for i in range(ParameterValueTest.TEST_ITERATIONS):
            value = np.int16(self.rnd.uniform(*ParameterValueTest.RANGE_16_BIT))
            bytes = struct.pack('<h', value)
            P = c3d.Param('INT16_TEST', self.dtypes, bytes_per_element=2, dimensions=[1], bytes=bytes)
            value_out = P.int16_value
            assert value == value_out, 'Parameter int16 was not read correctly. Was %f, expected %f' %\
                (value_out, value)

    def test_b_param_uint16(self):
        '''    Verify a single 16 bit unsigned integer value is parsed correctly
        '''
        for i in range(ParameterValueTest.TEST_ITERATIONS):
            value = np.uint16(self.rnd.uniform(*ParameterValueTest.RANGE_16_UNSIGNED_BIT))
            bytes = struct.pack('<H', value)
            P = c3d.Param('UINT16_TEST', self.dtypes, bytes_per_element=2, dimensions=[1], bytes=bytes)
            value_out = P.uint16_value
            assert value == value_out, 'Parameter uint16 was not read correctly. Was %f, expected %f' %\
                (value_out, value)

    def test_b_param_int8(self):
        '''    Verify a single 8 bit integer value is parsed correctly
        '''
        for i in range(ParameterValueTest.TEST_ITERATIONS):
            value = np.int8(self.rnd.uniform(*ParameterValueTest.RANGE_8_BIT))
            bytes = struct.pack('<b', value)
            P = c3d.Param('INT8_TEST', self.dtypes, bytes_per_element=1, dimensions=[1], bytes=bytes)
            value_out = P.int8_value
            assert value == value_out, 'Parameter int8 was not read correctly. Was %f, expected %f' %\
                (value_out, value)

    def test_b_param_uint8(self):
        '''    Verify a single 8 bit unsigned integer value is parsed correctly
        '''
        for i in range(ParameterValueTest.TEST_ITERATIONS):
            value = np.uint8(self.rnd.uniform(*ParameterValueTest.RANGE_8_UNSIGNED_BIT))
            bytes = struct.pack('<B', value)
            P = c3d.Param('UINT8_TEST', self.dtypes, bytes_per_element=1, dimensions=[1], bytes=bytes)
            value_out = P.uint8_value
            assert value == value_out, 'Parameter uint8 was not read correctly. Was %f, expected %f' %\
                (value_out, value)


class ParameterArrayTest(unittest.TestCase):
    '''    Test read Parameter arrays
    '''

    SHAPES = [[7, 6, 5], [7, 5, 3], [7, 3], [19]]

    def setUp(self):
        self.rnd = np.random.default_rng()
        self.dtypes = c3d.DataTypes(c3d.PROCESSOR_INTEL)

    def test_a_parse_float32_array(self):
        '''    Verify array of 32 bit floating point values are parsed correctly
        '''
        flt_range = (-1e6, 1e6)

        for shape in ParameterArrayTest.SHAPES:
            arr = self.rnd.uniform(flt_range[0], flt_range[1], size=shape).astype(np.float32)
            P = c3d.Param('FLOAT_TEST', self.dtypes, bytes_per_element=4, dimensions=arr.shape, bytes=arr.T.tobytes())
            arr_out = P.float_array
            assert arr.T.shape == arr_out.shape, "Mismatch in 'float_array' converted shape"
            assert np.all(arr.T == arr_out), 'Value mismatch when reading float array'

    def test_b_parse_int32_array(self):
        '''    Verify array of 32 bit integer values are parsed correctly
        '''
        flt_range = (-1e6, 1e6)

        for shape in ParameterArrayTest.SHAPES:
            arr = self.rnd.uniform(flt_range[0], flt_range[1], size=shape).astype(np.int32)
            P = c3d.Param('INT32_TEST', self.dtypes, bytes_per_element=4, dimensions=arr.shape, bytes=arr.T.tobytes())
            arr_out = P.int32_array
            assert arr.T.shape == arr_out.shape, "Mismatch in 'int32_array' converted shape"
            assert np.all(arr.T == arr_out), 'Value mismatch when reading int32 array'

    def test_c_parse_uint32_array(self):
        '''    Verify array of 32 bit unsigned integer values are parsed correctly
        '''
        flt_range = (0, 1e6)

        for shape in ParameterArrayTest.SHAPES:
            arr = self.rnd.uniform(flt_range[0], flt_range[1], size=shape).astype(np.uint32)
            P = c3d.Param('UINT32_TEST', self.dtypes, bytes_per_element=4, dimensions=arr.shape, bytes=arr.T.tobytes())
            arr_out = P.uint32_array
            assert arr.T.shape == arr_out.shape, "Mismatch in 'uint32_array' converted shape"
            assert np.all(arr.T == arr_out), 'Value mismatch when reading uint32 array'

    def test_d_parse_int16_array(self):
        '''    Verify array of 16 bit integer values are parsed correctly
        '''
        flt_range = (-1e4, 1e4)

        for shape in ParameterArrayTest.SHAPES:
            arr = self.rnd.uniform(flt_range[0], flt_range[1], size=shape).astype(np.int16)
            P = c3d.Param('INT16_TEST', self.dtypes, bytes_per_element=2, dimensions=arr.shape, bytes=arr.T.tobytes())
            arr_out = P.int16_array
            assert arr.T.shape == arr_out.shape, "Mismatch in 'int32_array' converted shape"
            assert np.all(arr.T == arr_out), 'Value mismatch when reading int32 array'

    def test_e_parse_uint16_array(self):
        '''    Verify array of 16 bit unsigned integer values are parsed correctly
        '''
        flt_range = (0, 1e4)

        for shape in ParameterArrayTest.SHAPES:
            arr = self.rnd.uniform(flt_range[0], flt_range[1], size=shape).astype(np.uint16)
            P = c3d.Param('UINT16_TEST', self.dtypes, bytes_per_element=2, dimensions=arr.shape, bytes=arr.T.tobytes())
            arr_out = P.uint16_array
            assert arr.T.shape == arr_out.shape, "Mismatch in 'uint32_array' converted shape"
            assert np.all(arr.T == arr_out), 'Value mismatch when reading uint32 array'

    def test_e_parse_int8_array(self):
        '''    Verify array of 8 bit integer values are parsed correctly
        '''
        flt_range = (-127, 127)

        for shape in ParameterArrayTest.SHAPES:
            arr = self.rnd.uniform(flt_range[0], flt_range[1], size=shape).astype(np.int8)
            P = c3d.Param('INT8_TEST', self.dtypes, bytes_per_element=1, dimensions=arr.shape, bytes=arr.T.tobytes())
            arr_out = P.int8_array
            assert arr.T.shape == arr_out.shape, "Mismatch in 'int32_array' converted shape"
            assert np.all(arr.T == arr_out), 'Value mismatch when reading int32 array'

    def test_f_parse_uint8_array(self):
        '''    Verify array of 8 bit unsigned integer values are parsed correctly
        '''
        flt_range = (0, 255)

        for shape in ParameterArrayTest.SHAPES:
            arr = self.rnd.uniform(flt_range[0], flt_range[1], size=shape).astype(np.uint8)
            P = c3d.Param('UINT8_TEST', self.dtypes, bytes_per_element=1, dimensions=arr.shape, bytes=arr.T.tobytes())
            arr_out = P.uint8_array
            assert arr.T.shape == arr_out.shape, "Mismatch in 'uint32_array' converted shape"
            assert np.all(arr.T == arr_out), 'Value mismatch when reading uint32 array'

    def test_g_parse_byte_array(self):
        '''    Verify byte arrays are parsed correctly
        '''
        word = b'WRIST'

        # 1 dims
        arr = np.array(word).repeat(3).repeat(3).repeat(3)
        P = c3d.Param('BYTE_TEST', self.dtypes, bytes_per_element=1, dimensions=arr.shape, bytes=arr.T.tobytes())
        arr_out = P.bytes_array
        assert arr.shape[1:] == arr_out.shape, "Mismatch in 'bytes_array' converted shape"
        assert np.all(arr.tobytes() == arr_out), 'Mismatch in reading single dimensional byte array'

        # 4 dims
        arr, shape = genByteWordArr(word, [5, 4, 3])
        P = c3d.Param('BYTE_TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
        arr_out = P.bytes_array

        assert arr.T.shape == arr_out.shape, "Mismatch in 'bytes_array' converted shape. Was %s, expected %s" %\
            (str(arr_out.shape), str(arr.T.shape))
        for i in np.ndindex(arr_out.shape):
            assert np.all(arr[i[::-1]] == arr_out[i]), "Mismatch in 'bytes_array' converted value at index %s" % str(i)

        # 5 dims
        arr, shape = genByteWordArr(word, [6, 5, 4, 3])
        P = c3d.Param('BYTE_TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
        arr_out = P.bytes_array

        assert arr.T.shape == arr_out.shape, "Mismatch in 'bytes_array' converted shape. Was %s, expected %s" %\
            (str(arr_out.shape), str(arr.T.shape))
        for i in np.ndindex(arr_out.shape):
            assert np.all(arr[i[::-1]] == arr_out[i]), "Mismatch in 'bytes_array' converted value at index %s" % str(i)

    def test_h_parse_string_array(self):
        '''    Verify repeated word arrays are parsed correctly
        '''
        word = b'ANCLE'

        # 3 dims
        arr, shape = genByteWordArr(word, [7, 3])
        P = c3d.Param('STRING_TEST', self.dtypes, bytes_per_element=-1, dimensions=shape, bytes=arr.T.tobytes())
        arr_out = P.string_array

        assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
            (str(arr_out.shape), str(arr.T.shape))
        for i in np.ndindex(arr_out.shape):
            assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
                "Mismatch in 'string_array' converted value at index %s" % str(i)

        # 4 dims
        arr, shape = genByteWordArr(word, [5, 4, 3])
        P = c3d.Param('STRING_TEST', self.dtypes, bytes_per_element=-1, dimensions=shape, bytes=arr.T.tobytes())
        arr_out = P.string_array

        assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
            (str(arr_out.shape), str(arr.T.shape))
        for i in np.ndindex(arr_out.shape):
            assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
                "Mismatch in 'string_array' converted value at index %s" % str(i)

        # 5 dims
        arr, shape = genByteWordArr(word, [6, 5, 4, 3])
        P = c3d.Param('STRING_TEST', self.dtypes, bytes_per_element=-1, dimensions=shape, bytes=arr.T.tobytes())
        arr_out = P.string_array

        assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
            (str(arr_out.shape), str(arr.T.shape))
        for i in np.ndindex(arr_out.shape):
            assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
                "Mismatch in 'string_array' converted value at index %s" % str(i)

    def test_i_parse_random_string_array(self):
        '''    Verify random word arrays are parsed correctly
        '''
        ##
        # RND

        # 3 dims
        for wlen in range(10):
            arr, shape = genRndByteArr(wlen, [7, 3], wlen > 5)
            P = c3d.Param('STRING_TEST', self.dtypes, bytes_per_element=-1, dimensions=shape, bytes=arr.T.tobytes())
            arr_out = P.string_array

            assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
                (str(arr_out.shape), str(arr.T.shape))
            for i in np.ndindex(arr_out.shape):
                assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
                    "Mismatch in 'string_array' converted value at index %s" % str(i)

        # 4 dims
        for wlen in range(10):
            arr, shape = genRndByteArr(wlen, [7, 5, 3], wlen > 5)
            P = c3d.Param('STRING_TEST', self.dtypes, bytes_per_element=-1, dimensions=shape, bytes=arr.T.tobytes())
            arr_out = P.string_array

            assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
                (str(arr_out.shape), str(arr.T.shape))
            for i in np.ndindex(arr_out.shape):
                assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
                    "Mismatch in 'string_array' converted value at index %s" % str(i)

        # 5 dims
        for wlen in range(10):
            arr, shape = genRndByteArr(wlen, [7, 6, 5, 3], wlen > 5)
            P = c3d.Param('STRING_TEST', self.dtypes, bytes_per_element=-1, dimensions=shape, bytes=arr.T.tobytes())
            arr_out = P.string_array

            assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
                (str(arr_out.shape), str(arr.T.shape))
            for i in np.ndindex(arr_out.shape):
                assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
                    "Mismatch in 'string_array' converted value at index %s" % str(i)


if __name__ == '__main__':
    unittest.main()
