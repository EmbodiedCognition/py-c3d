import c3d
import climate
import io
import os
import tempfile
import unittest
import urllib
import zipfile

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


class ReaderTest(Base):
    def test_format_pi(self):
        r = c3d.Reader(self._get('formats.zip', 'Eb015pi.c3d'))
        print(r.header)
        assert r.points_per_frame() == 26
        assert r.frame_rate() == 50

    def test_format_pr(self):
        r = c3d.Reader(self._get('formats.zip', 'Eb015pr.c3d'))
        print(r.header)
        assert r.points_per_frame() == 26
        assert r.frame_rate() == 50

    def test_paramsa(self):
        r = c3d.Reader(self._get('params.zip', 'TESTAPI.c3d'))
        print(r.header)
        assert r.points_per_frame() == 26
        assert r.frame_rate() == 50

    def test_paramsb(self):
        r = c3d.Reader(self._get('params.zip', 'TESTBPI.c3d'))
        print(r.header)
        for g in r._groups.values():
            for p in g._params.values():
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
        assert r.points_per_frame() == 26
        assert r.frame_rate() == 50
        assert r.analog_per_frame() == 16
        assert r.get_float('POINT:RATE') == 50
        assert r.get_float('ANALOG:RATE') == 200

    def test_paramsc(self):
        r = c3d.Reader(self._get('params.zip', 'TESTCPI.c3d'))
        print(r.header)
        assert r.points_per_frame() == 26
        assert r.frame_rate() == 50

    def test_paramsd(self):
        r = c3d.Reader(self._get('params.zip', 'TESTDPI.c3d'))
        print(r.header)
        assert r.points_per_frame() == 26
        assert r.frame_rate() == 50


class WriterTest(Base):
    def test_paramsd(self):
        r = c3d.Reader(self._get('params.zip', 'TESTDPI.c3d'))
        w = c3d.Writer(
            point_frame_rate=r.frame_rate(),
            analog_frame_rate=r.analog_frame_rate(),
            point_scale_factor=r.scale_factor(),
            gen_scale=r.get_float('ANALOG:GEN_SCALE'),
        )
        w.add_frames((p, a) for _, p, a in r.read_frames())
        h = io.BytesIO()
        w.write(h)


if __name__ == '__main__':
    unittest.main()
