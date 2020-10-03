import c3d
import importlib
climate_spec = importlib.util.find_spec("climate")
if climate_spec:
    import climate
import io
import os
import tempfile
import unittest
import urllib
import urllib.request
import zipfile
import numpy as np

# If climate exist
if climate_spec:
    logging = climate.get_logger('test')
    climate.enable_default_logging()

TEMP = os.path.join(tempfile.gettempdir(), 'c3d-test')
ZIPS = (
    ('https://www.c3d.org/data/sample01.zip', 'formats.zip'),
    ('https://www.c3d.org/data/sample07.zip', 'analog.zip'),
    ('https://www.c3d.org/data/sample08.zip', 'params.zip'),
)

class Base(unittest.TestCase):
    def setUp(self):
        if not os.path.isdir(TEMP):
            os.makedirs(TEMP)
        for url, target in ZIPS:
            fn = os.path.join(TEMP, target)
            print(fn)
            if not os.path.isfile(fn):
                try:
                    urllib.urlretrieve(url, fn)
                except AttributeError: # python 3
                    urllib.request.urlretrieve(url, fn)

    def _c3ds(self, zf):
        with zipfile.ZipFile(os.path.join(TEMP, zf)) as z:
            return [i for i in z.filelist
                    if i.filename.lower().endswith('.c3d')]

    def _get(self, zf, fn):
        with zipfile.ZipFile(os.path.join(TEMP, zf)) as z:
            return io.BytesIO(z.open(fn).read())

    def _log(self, r):
        print(r.header)
        items = ((k, v) for k, v in r.groups.items() if isinstance(k, str))
        fmt = '{0.name:>14s}:{1.name:<14s} {1.desc:36s} {2}'
        for _, g in sorted(items):
            for _, p in sorted(g.params.items()):
                value = None
                if p.bytes_per_element == 4:
                    if p.dimensions:
                        value = p.float_array
                    else:
                        value = p.float_value
                if p.bytes_per_element == 2:
                    if p.dimensions:
                        value = p.int16_array
                    else:
                        value = p.int16_value
                if p.bytes_per_element == 1:
                    if p.dimensions:
                        value = p.int8_array
                    else:
                        value = p.int8_value
                if p.bytes_per_element == -1:
                    if len(p.dimensions) > 1:
                        value = [s.strip() for s in p.string_array]
                    else:
                        value = p.string_value
                print(fmt.format(g, p, value))


class ReaderTest(Base):
    def test_format_pi(self):
        r = c3d.Reader(self._get('formats.zip', 'Eb015pi.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_format_pr(self):
        r = c3d.Reader(self._get('formats.zip', 'Eb015pr.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_paramsa(self):
        r = c3d.Reader(self._get('params.zip', 'TESTAPI.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_paramsb(self):
        r = c3d.Reader(self._get('params.zip', 'TESTBPI.c3d'))
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
        r = c3d.Reader(self._get('params.zip', 'TESTCPI.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_paramsd(self):
        r = c3d.Reader(self._get('params.zip', 'TESTDPI.c3d'))
        self._log(r)
        assert r.point_used == 26
        assert r.point_rate == 50

    def test_frames(self):
        r = c3d.Reader(self._get('params.zip', 'TESTDPI.c3d'))
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
    def test_paramsd(self):


        r = c3d.Reader(self._get('params.zip', 'TESTDPI.c3d'))
        w = c3d.Writer(
            point_rate=r.point_rate,
            analog_rate=r.analog_rate,
            point_scale=r.point_scale,
            gen_scale=r.get_float('ANALOG:GEN_SCALE'),
        )
        w.add_frames((p, a) for _, p, a in r.read_frames())

        ldata = r.get('POINT', None).get('LABELS', None)._as_any(np.uint8)#.flatten()
        l = [word.tostring().decode("ascii").strip() for word in ldata]
        h = io.BytesIO()
        w.write(h, l)


if __name__ == '__main__':
    unittest.main()
