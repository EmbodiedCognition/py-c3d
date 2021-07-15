''' Trailing utility functions.
'''
import numpy as np
import struct


def is_integer(value):
    '''Check if value input is integer.'''
    return isinstance(value, (int, np.int32, np.int64))


def is_iterable(value):
    '''Check if value is iterable.'''
    return hasattr(value, '__iter__')


def type_npy2struct(dtype):
    ''' Convert numpy dtype format to a struct package format string.
    '''
    return dtype.byteorder + dtype.char


def pack_labels(labels):
    ''' Static method used to pack and pad the set of `labels` strings before
        passing the output into a `c3d.group.Group.add_str`.

    Parameters
    ----------
    labels : iterable
        List of strings to pack and pad into a single string suitable for encoding in a Parameter entry.

    Example
    -------
    >>> labels = ['RFT1', 'RFT2', 'RFT3', 'LFT1', 'LFT2', 'LFT3']
    >>> param_str, label_max_size = Writer.pack_labels(labels)
    >>> writer.point_group.add_str('LABELS',
                                   'Point labels.',
                                   label_str,
                                   label_max_size,
                                   len(labels))

    Returns
    -------
    param_str : str
        String containing `labels` packed into a single variable where
        each string is padded to match the longest `labels` string.
    label_max_size : int
        Number of bytes associated with the longest `label` string, all strings are padded to this length.
    '''
    labels = np.ravel(labels)
    # Get longest label name
    label_max_size = 0
    label_max_size = max(label_max_size, np.max([len(label) for label in labels]))
    label_str = ''.join(label.ljust(label_max_size) for label in labels)
    return label_str, label_max_size


class Decorator(object):
    '''Base class for extending (decorating) a python object.
    '''
    def __init__(self, decoratee):
        self._decoratee = decoratee

    def __getattr__(self, name):
        return getattr(self._decoratee, name)


def UNPACK_FLOAT_IEEE(uint_32):
    '''Unpacks a single 32 bit unsigned int to a IEEE float representation
    '''
    return struct.unpack('f', struct.pack("<I", uint_32))[0]


def UNPACK_FLOAT_MIPS(uint_32):
    '''Unpacks a single 32 bit unsigned int to a IEEE float representation
    '''
    return struct.unpack('f', struct.pack(">I", uint_32))[0]


def DEC_to_IEEE(uint_32):
    '''Convert the 32 bit representation of a DEC float to IEEE format.

    Params:
    ----
    uint_32 : 32 bit unsigned integer containing the DEC single precision float point bits.
    Returns : IEEE formated floating point of the same shape as the input.
    '''
    # Follows the bit pattern found:
    # 	http://home.fnal.gov/~yang/Notes/ieee_vs_dec_float.txt
    # Further formating descriptions can be found:
    # 	http://www.irig106.org/docs/106-07/appendixO.pdf
    # In accodance with the first ref. first & second 16 bit words are placed
    # in a big endian 16 bit word representation, and needs to be inverted.
    # Second reference describe the DEC->IEEE conversion.

    # Warning! Unsure if NaN numbers are managed appropriately.

    # Shuffle the first two bit words from DEC bit representation to an ordered representation.
    # Note that the most significant fraction bits are placed in the first 7 bits.
    #
    # Below are the DEC layout in accordance with the references:
    # ___________________________________________________________________________________
    # |		Mantissa (16:0)		|	SIGN	|	Exponent (8:0)	|	Mantissa (23:17)	|
    # ___________________________________________________________________________________
    # |32-					  -16|	 15	   |14-				  -7|6-					  -0|
    #
    # Legend:
    # _______________________________________________________
    # | Part (left bit of segment : right bit) | Part | ..
    # _______________________________________________________
    # |Bit adress -     ..       - Bit adress | Bit adress - ..
    ####

    # Swap the first and last 16  bits for a consistent alignment of the fraction
    reshuffled = ((uint_32 & 0xFFFF0000) >> 16) | ((uint_32 & 0x0000FFFF) << 16)
    # After the shuffle each part are in little-endian and ordered as: SIGN-Exponent-Fraction
    exp_bits = ((reshuffled & 0xFF000000) - 1) & 0xFF000000
    reshuffled = (reshuffled & 0x00FFFFFF) | exp_bits
    return UNPACK_FLOAT_IEEE(reshuffled)


def DEC_to_IEEE_BYTES(bytes):
    '''Convert byte array containing 32 bit DEC floats to IEEE format.

    Params:
    ----
    bytes : Byte array where every 4 bytes represent a single precision DEC float.
    Returns : IEEE formated floating point of the same shape as the input.
    '''

    # See comments in DEC_to_IEEE() for DEC format definition

    # Reshuffle
    bytes = memoryview(bytes)
    reshuffled = np.empty(len(bytes), dtype=np.dtype('B'))
    reshuffled[::4] = bytes[2::4]
    reshuffled[1::4] = bytes[3::4]
    reshuffled[2::4] = bytes[::4]
    # Decrement exponent by 2, if exp. > 1
    reshuffled[3::4] = bytes[1::4] + (np.bitwise_and(bytes[1::4], 0x7f) == 0) - 1

    # There are different ways to adjust for differences in DEC/IEEE representation
    # after reshuffle. Two simple methods are:
    # 1) Decrement exponent bits by 2, then convert to IEEE.
    # 2) Convert to IEEE directly and divide by four.
    # 3) Handle edge cases, expensive in python...
    # However these are simple methods, and do not accurately convert when:
    # 1) Exponent < 2 (without bias), impossible to decrement exponent without adjusting fraction/mantissa.
    # 2) Exponent == 0, DEC numbers are then 0 or undefined while IEEE is not. NaN are produced when exponent == 255.
    # Here method 1) is used, which mean that only small numbers will be represented incorrectly.

    return np.frombuffer(reshuffled.tobytes(),
                         dtype=np.float32,
                         count=int(len(bytes) / 4))
