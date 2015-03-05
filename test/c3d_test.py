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


class ReaderTest(unittest.TestCase):
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

    def test_format(self):
        for fn in self._c3ds('formats.zip'):
            try:
                r = c3d.Reader(self._get('formats.zip', fn))
            except Exception as e:
                logging.exception('formats.zip:{}'.format(fn.filename))
                assert False
                continue
            print(r.header)
            assert r.points_per_frame() == 12

    def test_params(self):
        for fn in self._c3ds('params.zip'):
            try:
                r = c3d.Reader(self._get('params.zip', fn))
            except Exception as e:
                logging.exception('params.zip:{}'.format(fn.filename))
                assert False
                continue
            print(r)
            assert r.points_per_frame() == 12


class WriterTest(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
