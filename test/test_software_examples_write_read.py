''' Tests
'''

import c3d
import unittest
import os
import test.verify as verify
from test.base import Base
from test.zipload import Zipload, TEMP


def verify_read_write(zip, file_path, proc_type='INTEL', real=True):
    ''' Compare read write ouput to original read file.
    '''
    A = c3d.Reader(Zipload._get(zip, file_path))

    cpy_mode = 'copy'
    if proc_type != 'INTEL':
        cpy_mode = 'shallow_copy'
    writer = A.to_writer(cpy_mode)

    tmp_path = os.path.join(TEMP, 'write_test.c3d')
    with open(tmp_path, 'wb') as handle:
        writer.write(handle)

    aname = 'Original'
    bname = 'WriteRead'
    test_id = '{} write read test'.format(proc_type)

    with open(tmp_path, 'rb') as handle:
        B = c3d.Reader(handle)
        verify.equal_headers(test_id, A, B, aname, bname, real, real)
        verify.data_is_equal(A, B, aname, bname)


class Sample00(Base):

    ZIP = 'sample00.zip'
    zip_files = \
        [
         ('Advanced Realtime Tracking GmbH', ['arthuman-sample.c3d', 'arthuman-sample-fingers.c3d']),
         ('Codamotion', ['codamotion_gaitwands_19970212.c3d', 'codamotion_gaitwands_20150204.c3d']),
         ('Cometa Systems', ['EMG Data Cometa.c3d']),
         ('Innovative Sports Training', ['Gait with EMG.c3d', 'Static Pose.c3d']),
         ('Motion Analysis Corporation', ['Sample_Jump2.c3d', 'Walk1.c3d']),
         ('NexGen Ergonomics', ['test1.c3d']),
         # Vicon files are weird, uses non-standard encodings. Walking01.c3d contain nan values.
         ('Vicon Motion Systems', ['pyCGM2 lower limb CGM24 Walking01.c3d', 'TableTennis.c3d']),
        ]

    def test_read_write_examples(self):
        return
        ''' Compare write ouput to original read
        '''

        print('----------------------------')
        print(type(self))
        print('----------------------------')
        for folder, files in self.zip_files:
            print('{} | Validating...'.format(folder))
            for file in files:
                verify_read_write(self.ZIP, '{}/{}'.format(folder, file))
            print('... OK')
        print('DONE')


class Sample01(Base):

    ZIP = 'sample01.zip'
    zip_files = \
        [
         ('Eb015pi.c3d', 'INTEL', False),
         ('Eb015pr.c3d', 'INTEL', True),
         ('Eb015vi.c3d', 'DEC', False),
         ('Eb015vr.c3d', 'DEC', True),
         ('Eb015si.c3d', 'SGI', False),
         ('Eb015sr.c3d', 'SGI', True),
        ]

    def test_read_write_examples(self):
        ''' Compare write ouput to original read
        '''
        print('----------------------------')
        print(type(self))
        print('----------------------------')
        for (file, proc, is_real) in self.zip_files:
            print('{} | Validating...'.format(file))
            verify_read_write(self.ZIP, file, proc, is_real)
            print('... OK')
        print('Done.')



if __name__ == '__main__':
    unittest.main()
