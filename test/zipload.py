import io
import os
import tempfile
import urllib
import urllib.request
import zipfile

TEMP = os.path.join(tempfile.gettempdir(), 'c3d-test')
ZIPS = (
    ('https://www.c3d.org/data/Sample00.zip', 'sample00.zip'),
    ('https://www.c3d.org/data/sample01.zip', 'sample01.zip'),
    ('https://www.c3d.org/data/sample02.zip', 'sample02.zip'),
    ('https://www.c3d.org/data/sample07.zip', 'sample07.zip'),
    ('https://www.c3d.org/data/sample08.zip', 'sample08.zip'),
    ('https://www.c3d.org/data/sample19.zip', 'sample19.zip'),
    ('https://www.c3d.org/data/sample31.zip', 'sample31.zip'),
    ('https://www.c3d.org/data/Sample36.zip', 'sample36.zip'),
)


class Zipload():

    def download():
        if not os.path.isdir(TEMP):
            os.makedirs(TEMP)
        for url, target in ZIPS:
            fn = os.path.join(TEMP, target)
            if not os.path.isfile(fn):
                print('Downloading: ', url)
                try:
                    urllib.urlretrieve(url, fn)
                except AttributeError:  # python 3
                    urllib.request.urlretrieve(url, fn)
                print('... Complete')

    def extract(zf):
        out_path = os.path.join(TEMP, os.path.basename(zf)[:-4])

        zip = zipfile.ZipFile(os.path.join(TEMP, zf))
        # Loop equivalent to zip.extractall(out_path) but avoids overwriting files
        for zf in zip.namelist():
            fpath = os.path.join(out_path, zf)
            # If file already exist, don't extract
            if not os.path.isfile(fpath) and not os.path.isdir(fpath):
                print('Extracted:', fpath)
                zip.extract(zf, path=out_path)

    def _c3ds(zf):
        with zipfile.ZipFile(os.path.join(TEMP, zf)) as z:
            return [i for i in z.filelist
                    if i.filename.lower().endswith('.c3d')]

    def _get(zf, fn):
        with zipfile.ZipFile(os.path.join(TEMP, zf)) as z:
            return io.BytesIO(z.open(fn).read())
