''' Basic Reader and Writer tests.
'''
import c3d
import importlib
import io
import unittest
import numpy as np
from test.base import Base
from test.zipload import Zipload
climate_spec = importlib.util.find_spec("climate")
if climate_spec:
    import climate

# If climate exist
if climate_spec:
    logging = climate.get_logger('test')
    climate.enable_default_logging()


class ReaderTest(Base):
    ''' Test basic Reader functionality
    '''
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
        for g in r.group_values():
            for p in g.param_values():
                if len(p.dimensions) == 0:
                    val = None
                    width = len(p.bytes_data)
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


class WriterTest(Base):
    ''' Test basic writer functionality
    '''
    def test_add_frames(self):
        r = c3d.Reader(Zipload._get('sample08.zip', 'TESTDPI.c3d'))
        w = c3d.Writer(
            point_rate=r.point_rate,
            analog_rate=r.analog_rate,
            point_scale=r.point_scale,
            gen_scale=r.get_float('ANALOG:GEN_SCALE'),
        )
        w.add_frames([(p, a) for _, p, a in r.read_frames()])
        w.add_frames([(p, a) for _, p, a in r.read_frames()], index=5)

        h = io.BytesIO()
        w.set_point_labels(r.point_labels)
        w.set_analog_labels(r.analog_labels)
        w.write(h)

    def test_set_params(self):
        r = c3d.Reader(Zipload._get('sample08.zip', 'TESTDPI.c3d'))
        w = c3d.Writer(
            point_rate=r.point_rate,
            analog_rate=r.analog_rate,
            point_scale=r.point_scale,
            gen_scale=r.get_float('ANALOG:GEN_SCALE'),
        )
        w.add_frames([(p, a) for _, p, a in r.read_frames()])

        h = io.BytesIO()
        w.set_start_frame(255)
        w.set_point_labels(r.point_labels)
        w.set_analog_labels(r.analog_labels)

        # Screen axis
        X, Y = '-Y', '+Z'
        w.set_screen_axis()
        w.set_screen_axis(X, Y)
        X_v, Y_v = w.get_screen_axis()
        assert X_v == X and Y == Y_v, 'Mismatch between set & get screen axis.'

        assert np.all(np.equal(r.point_labels, w.point_labels)), 'Expected labels to be equal.'

        w.write(h)

if __name__ == '__main__':
    unittest.main()
