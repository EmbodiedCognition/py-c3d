''' Tests
'''

import c3d
import unittest
import os
import test.verify as verify
from test.base import Base
from test.zipload import Zipload, TEMP

class Sample00(Base):
    ZIP = 'sample00.zip'

    DATA_RANGE = (-1e6, 1e6)
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

    def verify_read_write(self, file_path):
        ''' Compare read write ouput to original read file.
        '''
        A = c3d.Reader(Zipload._get(self.ZIP, file_path))
        writer = A.to_writer('copy')

        tmp_path = os.path.join(TEMP, 'write_test.c3d')
        with open(tmp_path, 'wb') as handle:
            writer.write(handle)

        proc_type = 'INTEL'
        aname = 'Original'
        bname = 'WriteRead'
        test_id = '{} write read test'.format(proc_type)

        with open(tmp_path, 'rb') as handle:
            B = c3d.Reader(handle)
            verify.equal_headers(test_id, A, B, aname, bname, True, True)
            verify.data_is_equal(A, B, aname, bname)



    def test_read_write_examples(self):
        ''' Compare write ouput to original read
        '''

        print('----------------------------')
        print(type(self))
        print('----------------------------')
        for folder, files in self.zip_files:
            print('{} | Validating...'.format(folder))
            for file in files:
                self.verify_read_write('{}/{}'.format(folder, file))
            print('... OK')
        print('DONE')


if __name__ == '__main__':
    unittest.main()
