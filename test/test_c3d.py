import c3d
import importlib
climate_spec = importlib.util.find_spec("climate")
if climate_spec:
    import climate
import io
import os
import unittest
import numpy as np
from test.base import Base
from test.zipload import Zipload

# If climate exist
if climate_spec:
    logging = climate.get_logger('test')
    climate.enable_default_logging()


class A_ReaderTest(Base):
    def test_format_pi(self):
        r = c3d.Reader(Zipload._get('sample01.zip', 'Eb015pi.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_format_pr(self):
        r = c3d.Reader(Zipload._get('sample01.zip', 'Eb015pr.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_paramsa(self):
        r = c3d.Reader(Zipload._get('sample08.zip', 'TESTAPI.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_paramsb(self):
        r = c3d.Reader(Zipload._get('sample08.zip', 'TESTBPI.c3d'))
        self._log(r)
        for g in r.groups.values():
            for p in g.params.values():
                if len(p.dimensions) == 0:
                    val = None
                    width = len(p.bytes)
                    if width == 2:
                        val = p.int16_value
                    elif width == 4:
                        val = p.float_value
                    else:
                        val = p.int8_value
                    print('{0.name}.{1.name} = {2}'.format(g, p, val))
        assert r.point_used == 26
        assert r.point_rate == 50
        assert r.analog_used == 16
        assert r.get_float('POINT:RATE') == 50
        assert r.get_float('ANALOG:RATE') == 200

    def test_paramsc(self):
        r = c3d.Reader(Zipload._get('sample08.zip', 'TESTCPI.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_paramsd(self):
        r = c3d.Reader(Zipload._get('sample08.zip', 'TESTDPI.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_frames(self):
        r = c3d.Reader(Zipload._get('sample08.zip', 'TESTDPI.c3d'))
        self._log(r)
        frames = list(r.read_frames())
        assert len(frames) == 450
        frame_no, points, analog = frames[0]
        assert frame_no == 1, frame_no
        expected = (r.point_used, 5)
        assert points.shape == expected, \
            'point shape: got {}, expected {}'.format(points.shape, expected)
        expected = (r.analog_used, r.header.analog_per_frame)
        assert analog.shape == expected, \
            'analog shape: got {}, expected {}'.format(analog.shape, expected)


class B_WriterTest(Base):
    def test_paramsd(self):


        r = c3d.Reader(Zipload._get('sample08.zip', 'TESTDPI.c3d'))
        w = c3d.Writer(
            point_rate=r.point_rate,
            analog_rate=r.analog_rate,
            point_scale=r.point_scale,
            gen_scale=r.get_float('ANALOG:GEN_SCALE'),
        )
        w.add_frames((p, a) for _, p, a in r.read_frames())

        h = io.BytesIO()
        w.write(h, r.point_labels)

class C_FormatTest(Base):
    def test_intel(self):

        FMT_INTEL_INT = c3d.Reader(Zipload._get('sample01.zip', 'Eb015pi.c3d'))
        FMT_INTEL_REAL = c3d.Reader(Zipload._get('sample01.zip', 'Eb015pr.c3d'))

        proc_type = 'INTEL'

        Base.compare_header('{} format test'.format(proc_type),
            FMT_INTEL_INT, FMT_INTEL_REAL, 'INT', 'REAL', False, True)

        Base.compare_data(FMT_INTEL_INT, FMT_INTEL_REAL)

        print('----------------------------')
        print('INTEL FORMAT: OK')

    def test_dec(self):

        FMT_DEC_INT = c3d.Reader(Zipload._get('sample01.zip', 'Eb015vi.c3d'))
        FMT_DEC_REAL = c3d.Reader(Zipload._get('sample01.zip', 'Eb015vr.c3d'))

        proc_type = 'DEC'

        Base.compare_header('{} format test'.format(proc_type),
            FMT_DEC_INT, FMT_DEC_REAL, 'INT', 'REAL', False, True)

        Base.compare_data(FMT_DEC_INT, FMT_DEC_REAL)

        print('----------------------------')
        print('DEC FORMAT: OK')


    def test_sgi(self):

        FMT_SGI_INT = c3d.Reader(Zipload._get('sample01.zip', 'Eb015si.c3d'))
        FMT_SGI_REAL = c3d.Reader(Zipload._get('sample01.zip', 'Eb015sr.c3d'))

        proc_type = 'SGI'

        Base.compare_header('{} format test'.format(proc_type),
            FMT_SGI_INT, FMT_SGI_REAL, 'INT', 'REAL', False, True)

        Base.compare_data(FMT_SGI_INT, FMT_SGI_REAL)

        print('----------------------------')
        print('SGI FORMAT: OK')

    def test_int_formats(self):

        FMT_INTEL_INT = c3d.Reader(Zipload._get('sample01.zip', 'Eb015pi.c3d'))
        FMT_DEC_INT = c3d.Reader(Zipload._get('sample01.zip', 'Eb015vi.c3d'))
        FMT_SGI_INT = c3d.Reader(Zipload._get('sample01.zip', 'Eb015si.c3d'))

        Base.compare_header('INTEL-DEC INT format test', FMT_INTEL_INT, FMT_DEC_INT, 'INTEL', 'DEC', False, False)
        Base.compare_header('INTEL-SGI INT format test', FMT_INTEL_INT, FMT_SGI_INT, 'INTEL', 'SGI', False, False)
        Base.compare_header('DEC-SGI INT format test', FMT_DEC_INT, FMT_SGI_INT, 'DEC', 'SGI', False, False)

        Base.compare_data(FMT_INTEL_INT, FMT_DEC_INT)
        Base.compare_data(FMT_INTEL_INT, FMT_SGI_INT)
        Base.compare_data(FMT_DEC_INT, FMT_SGI_INT)

        print('----------------------------')
        print('INTEL-DEC-SGI INT FORMAT COMPARISON: OK')

    def test_real_formats(self):


        FMT_INTEL_REAL = c3d.Reader(Zipload._get('sample01.zip', 'Eb015pr.c3d'))
        FMT_DEC_REAL = c3d.Reader(Zipload._get('sample01.zip', 'Eb015vr.c3d'))
        FMT_SGI_REAL = c3d.Reader(Zipload._get('sample01.zip', 'Eb015sr.c3d'))

        Base.compare_header('INTEL-DEC INT format test', FMT_INTEL_REAL, FMT_DEC_REAL, 'INTEL', 'DEC', True, True)
        Base.compare_header('INTEL-SGI INT format test', FMT_INTEL_REAL, FMT_SGI_REAL, 'INTEL', 'SGI', True, True)
        Base.compare_header('DEC-SGI INT format test', FMT_DEC_REAL, FMT_SGI_REAL, 'DEC', 'SGI', True, True)

        Base.compare_data(FMT_INTEL_REAL, FMT_DEC_REAL)
        Base.compare_data(FMT_INTEL_REAL, FMT_SGI_REAL)
        Base.compare_data(FMT_DEC_REAL, FMT_SGI_REAL)

        print('----------------------------')
        print('INTEL-DEC-SGI REAL FORMAT COMPARISON: OK')

if __name__ == '__main__':
    unittest.main()
