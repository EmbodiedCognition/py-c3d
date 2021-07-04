'''
State object defining the data types associated with a given .c3d processor format.
'''

import sys
import codecs
import numpy as np

PROCESSOR_INTEL = 84
PROCESSOR_DEC = 85
PROCESSOR_MIPS = 86


class DataTypes(object):
    ''' Container defining the data types used when parsing byte data.
        Data types depend on the processor format the file is stored in.
    '''
    def __init__(self, proc_type=PROCESSOR_INTEL):
        self._proc_type = proc_type
        self._little_endian_sys = sys.byteorder == 'little'
        self._native = ((self.is_ieee or self.is_dec) and self.little_endian_sys) or \
                       (self.is_mips and self.big_endian_sys)
        if self.big_endian_sys:
            warnings.warn('Systems with native byte order of big-endian are not supported.')

        if self._proc_type == PROCESSOR_MIPS:
            # Big-Endian (SGI/MIPS format)
            self.float32 = np.dtype(np.float32).newbyteorder('>')
            self.float64 = np.dtype(np.float64).newbyteorder('>')
            self.uint8 = np.uint8
            self.uint16 = np.dtype(np.uint16).newbyteorder('>')
            self.uint32 = np.dtype(np.uint32).newbyteorder('>')
            self.uint64 = np.dtype(np.uint64).newbyteorder('>')
            self.int8 = np.int8
            self.int16 = np.dtype(np.int16).newbyteorder('>')
            self.int32 = np.dtype(np.int32).newbyteorder('>')
            self.int64 = np.dtype(np.int64).newbyteorder('>')
        else:
            # Little-Endian format (Intel or DEC format)
            self.float32 = np.float32
            self.float64 = np.float64
            self.uint8 = np.uint8
            self.uint16 = np.uint16
            self.uint32 = np.uint32
            self.uint64 = np.uint64
            self.int8 = np.int8
            self.int16 = np.int16
            self.int32 = np.int32
            self.int64 = np.int64

    @property
    def is_ieee(self) -> bool:
        ''' True if the associated file is in the Intel format.
        '''
        return self._proc_type == PROCESSOR_INTEL

    @property
    def is_dec(self) -> bool:
        ''' True if the associated file is in the DEC format.
        '''
        return self._proc_type == PROCESSOR_DEC

    @property
    def is_mips(self) -> bool:
        ''' True if the associated file is in the SGI/MIPS format.
        '''
        return self._proc_type == PROCESSOR_MIPS

    @property
    def proc_type(self) -> str:
        ''' Get the processory type associated with the data format in the file.
        '''
        processor_type = ['INTEL', 'DEC', 'MIPS']
        return processor_type[self._proc_type - PROCESSOR_INTEL]

    @property
    def processor(self) -> int:
        ''' Get the processor number encoded in the .c3d file.
        '''
        return self._proc_type

    @property
    def native(self) -> bool:
        ''' True if the native (system) byte order matches the file byte order.
        '''
        return self._native

    @property
    def little_endian_sys(self) -> bool:
        ''' True if native byte order is little-endian.
        '''
        return self._little_endian_sys

    @property
    def big_endian_sys(self) -> bool:
        ''' True if native byte order is big-endian.
        '''
        return not self._little_endian_sys

    def decode_string(self, bytes) -> str:
        ''' Decode a byte array to a string.
        '''
        # Attempt to decode using different decoders
        decoders = ['utf-8', 'latin-1']
        for dec in decoders:
            try:
                return codecs.decode(bytes, dec)
            except UnicodeDecodeError:
                continue
        # Revert to using default decoder but replace characters
        return codecs.decode(bytes, decoders[0], 'replace')
