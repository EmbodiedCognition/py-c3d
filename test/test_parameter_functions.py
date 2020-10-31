import c3d
import io
import os
import unittest
import numpy as np


def genWordMDArr(word, shape):
	'''	Generate a multi-dimensional byte array from a specific word.
	'''
	arr = np.array(word)
	for d in shape[::-1]:
		arr = arr[np.newaxis].repeat(d, 0)
	return arr, [len(word)] + [d for d in shape]

def genRndMDArr(wordlen, shape, pad):
	'''	Generate a multi-dimensional byte array with random data.
	'''
	tot_len = wordlen + pad*wordlen
	arr = np.empty(shape, dtype=np.dtype('S'+str(tot_len)))
	for i in np.ndindex(arr.shape):
		bytes = np.random.randint(21, 126, wordlen).astype(np.uint8)
		if pad:
			bytes = np.hstack((bytes, np.array([b'255']*wordlen, dtype=np.uint8)))
		arr[i] = bytes.tobytes()
	return arr, [tot_len] + [d for d in shape]

class ParameterTest(unittest.TestCase):
	def setUp(self):
		self.rnd = np.random.default_rng()
		self.dtypes = c3d.DataTypes(c3d.PROCESSOR_INTEL)

	def test_a_parse_byte_array(self):
		'''	Verify byte arrays are parsed correctly
		'''
		word = b'WRIST'

		# 1 dims
		arr = np.array(word).repeat(3).repeat(3).repeat(3)
		P = c3d.Param('TEST', self.dtypes, bytes_per_element=1, dimensions=arr.shape, bytes=arr.T.tobytes())
		arr_out = P.bytes_array
		assert arr.shape[1:] == arr_out.shape, "Mismatch in 'bytes_array' converted shape"
		assert np.all(arr.tobytes() == arr_out), 'Mismatch in reading single dimensional byte array'

		# 4 dims
		arr, shape = genWordMDArr(word, [5, 4, 3])
		P = c3d.Param('TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
		arr_out = P.bytes_array

		assert arr.T.shape == arr_out.shape, "Mismatch in 'bytes_array' converted shape. Was %s, expected %s" %\
			(str(arr_out.shape), str(arr.T.shape))
		for i in np.ndindex(arr_out.shape):
			assert np.all(arr[i[::-1]] == arr_out[i]), "Mismatch in 'bytes_array' converted value at index %s" % str(i)

		# 5 dims
		arr, shape = genWordMDArr(word, [6, 5, 4, 3])
		P = c3d.Param('TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
		arr_out = P.bytes_array

		assert arr.T.shape == arr_out.shape, "Mismatch in 'bytes_array' converted shape. Was %s, expected %s" %\
			(str(arr_out.shape), str(arr.T.shape))
		for i in np.ndindex(arr_out.shape):
			assert np.all(arr[i[::-1]] == arr_out[i]), "Mismatch in 'bytes_array' converted value at index %s" % str(i)

	def test_b_parse_string_array(self):
		'''	Verify repeated word arrays are parsed correctly
		'''
		word = b'ANCLE'


		# 3 dims
		arr, shape = genWordMDArr(word, [7, 3])
		P = c3d.Param('TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
		arr_out = P.string_array

		assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
			(str(arr_out.shape), str(arr.T.shape))
		for i in np.ndindex(arr_out.shape):
			assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
				"Mismatch in 'string_array' converted value at index %s" % str(i)

		# 4 dims
		arr, shape = genWordMDArr(word, [5, 4, 3])
		P = c3d.Param('TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
		arr_out = P.string_array

		assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
			(str(arr_out.shape), str(arr.T.shape))
		for i in np.ndindex(arr_out.shape):
			assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
				"Mismatch in 'string_array' converted value at index %s" % str(i)

		# 5 dims
		arr, shape = genWordMDArr(word, [6, 5, 4, 3])
		P = c3d.Param('TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
		arr_out = P.string_array

		assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
			(str(arr_out.shape), str(arr.T.shape))
		for i in np.ndindex(arr_out.shape):
			assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
				"Mismatch in 'string_array' converted value at index %s" % str(i)

	def test_c_parse_random_string_array(self):
		'''	Verify random word arrays are parsed correctly
		'''
		##
		# RND

		# 3 dims
		for wlen in range(10):
			arr, shape = genRndMDArr(wlen, [7, 3], wlen > 5)
			P = c3d.Param('TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
			arr_out = P.string_array

			assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
				(str(arr_out.shape), str(arr.T.shape))
			for i in np.ndindex(arr_out.shape):
				assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
					"Mismatch in 'string_array' converted value at index %s" % str(i)

		# 4 dims
		for wlen in range(10):
			arr, shape = genRndMDArr(wlen, [7, 5, 3], wlen > 5)
			P = c3d.Param('TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
			arr_out = P.string_array

			assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
				(str(arr_out.shape), str(arr.T.shape))
			for i in np.ndindex(arr_out.shape):
				assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
					"Mismatch in 'string_array' converted value at index %s" % str(i)

		# 5 dims
		for wlen in range(10):
			arr, shape = genRndMDArr(wlen, [7, 6, 5, 3], wlen > 5)
			P = c3d.Param('TEST', self.dtypes, bytes_per_element=1, dimensions=shape, bytes=arr.T.tobytes())
			arr_out = P.string_array

			assert arr.T.shape == arr_out.shape, "Mismatch in 'string_array' converted shape. Was %s, expected %s" %\
				(str(arr_out.shape), str(arr.T.shape))
			for i in np.ndindex(arr_out.shape):
				assert self.dtypes.decode_string(arr[i[::-1]]) == arr_out[i],\
					"Mismatch in 'string_array' converted value at index %s" % str(i)



if __name__ == '__main__':
	unittest.main()
