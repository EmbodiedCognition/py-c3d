import c3d
import importlib
import io
import os
import unittest
import numpy as np
from test.base import Base
from test.zipload import Zipload

class FormatTest():
    ''' Test to evaluate INTEL, DEC and SGI/MIPS processor formats using a set of identical files.

        INTEL: IEEE standard floating points and little endian.
        DEC:   Non-standard floating point representation, standard integer representations.
        SGI:   IEEE standard but ordered in big endian.
    '''

    def test_a_intel(self):
        ''' Compare identical INTEL files encoded using both floating-point and integer representations.
        '''

        print('----------------------------')
        print(type(self))
        print('----------------------------')

        FMT_INTEL_INT = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_INT))
        FMT_INTEL_REAL = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))

        #self._log(FMT_INTEL_INT)
        #self._log(FMT_INTEL_REAL)
        proc_type = 'INTEL'
        test_id = '{} format test'.format(proc_type)

        Base.compare_header(test_id, FMT_INTEL_INT, FMT_INTEL_REAL, 'INT', 'REAL', False, True)
        Base.compare_data(FMT_INTEL_INT, FMT_INTEL_REAL, 'INT', 'REAL')

        print('INTEL FORMAT: OK')

    def test_b_dec(self):
        ''' Compare identical DEC files encoded using both floating-point and integer representations.
        '''

        FMT_DEC_INT = c3d.Reader(Zipload._get(self.ZIP, self.DEC_INT))
        FMT_DEC_REAL = c3d.Reader(Zipload._get(self.ZIP, self.DEC_REAL))

        proc_type = 'DEC'
        test_id = '{} format test'.format(proc_type)

        Base.compare_header(test_id, FMT_DEC_INT, FMT_DEC_REAL, 'INT', 'REAL', False, True)
        Base.compare_data(FMT_DEC_INT, FMT_DEC_REAL, 'INT', 'REAL')

        print('DEC FORMAT: OK')


    def test_c_sgi(self):
        ''' Compare identical SGI/MIPS files encoded using both floating-point and integer representations.
        '''

        FMT_SGI_INT = c3d.Reader(Zipload._get(self.ZIP, self.MIPS_INT))
        FMT_SGI_REAL = c3d.Reader(Zipload._get(self.ZIP, self.MIPS_REAL))

        proc_type = 'SGI'
        test_id = '{} format test'.format(proc_type)

        Base.compare_header(test_id, FMT_SGI_INT, FMT_SGI_REAL, 'INT', 'REAL', False, True)
        Base.compare_data(FMT_SGI_INT, FMT_SGI_REAL, 'INT', 'REAL')

        print('SGI FORMAT: OK')

    def test_d_int_formats(self):
        ''' Compare identical files for different processor formats.
            All files are encoded using the integer representations.
        '''

        FMT_INTEL_INT = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_INT))
        FMT_DEC_INT = c3d.Reader(Zipload._get(self.ZIP, self.DEC_INT))
        FMT_SGI_INT = c3d.Reader(Zipload._get(self.ZIP, self.MIPS_INT))

        Base.compare_header('INTEL-DEC INT format test', FMT_INTEL_INT, FMT_DEC_INT, 'INTEL', 'DEC', False, False)
        Base.compare_header('INTEL-SGI INT format test', FMT_INTEL_INT, FMT_SGI_INT, 'INTEL', 'SGI', False, False)
        Base.compare_header('DEC-SGI INT format test', FMT_DEC_INT, FMT_SGI_INT, 'DEC', 'SGI', False, False)

        Base.compare_data(FMT_INTEL_INT, FMT_DEC_INT, 'INTEL', 'DEC')
        Base.compare_data(FMT_INTEL_INT, FMT_SGI_INT, 'INTEL', 'SGI')
        Base.compare_data(FMT_DEC_INT, FMT_SGI_INT, 'DEC', 'SGI')

        print('INTEL-DEC-SGI INT FORMAT COMPARISON: OK')

    def test_e_real_formats(self):
        ''' Compare identical files for different processor formats.
            All files are encoded using the floating-point representations.
        '''


        FMT_INTEL_REAL = c3d.Reader(Zipload._get(self.ZIP, self.INTEL_REAL))
        FMT_DEC_REAL = c3d.Reader(Zipload._get(self.ZIP, self.DEC_REAL))
        FMT_SGI_REAL = c3d.Reader(Zipload._get(self.ZIP, self.MIPS_REAL))

        Base.compare_header('INTEL-DEC INT format test', FMT_INTEL_REAL, FMT_DEC_REAL, 'INTEL', 'DEC', True, True)
        Base.compare_header('INTEL-SGI INT format test', FMT_INTEL_REAL, FMT_SGI_REAL, 'INTEL', 'SGI', True, True)
        Base.compare_header('DEC-SGI INT format test', FMT_DEC_REAL, FMT_SGI_REAL, 'DEC', 'SGI', True, True)

        Base.compare_data(FMT_INTEL_REAL, FMT_DEC_REAL, 'INTEL', 'DEC')
        Base.compare_data(FMT_INTEL_REAL, FMT_SGI_REAL, 'INTEL', 'SGI')
        Base.compare_data(FMT_DEC_REAL, FMT_SGI_REAL, 'DEC', 'SGI')

        print('INTEL-DEC-SGI REAL FORMAT COMPARISON: OK')

class Sample01(FormatTest, Base):
    ZIP = 'sample01.zip'
    INTEL_INT = 'Eb015pi.c3d'
    INTEL_REAL = 'Eb015pr.c3d'
    DEC_INT = 'Eb015vi.c3d'
    DEC_REAL = 'Eb015vr.c3d'
    MIPS_INT = 'Eb015si.c3d'
    MIPS_REAL = 'Eb015sr.c3d'

class Sample02(FormatTest, Base):
    ZIP = 'sample02.zip'
    INTEL_INT = 'pc_int.c3d'
    INTEL_REAL = 'pc_real.c3d'
    DEC_INT = 'DEC_INT.C3D'
    DEC_REAL = 'Dec_real.c3d'
    MIPS_INT = 'sgi_int.c3d'
    MIPS_REAL = 'sgi_real.c3d'

if __name__ == '__main__':
    unittest.main()
