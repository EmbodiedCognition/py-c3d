import unittest
import test.verify as verify
from test.base import Base


class Sample00(verify.WithinRangeTest, Base):
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
         ('Vicon Motion Systems', ['TableTennis.c3d']),
         # Vicon files are weird, uses non-standard encodings. Walking01.c3d contain nan values and is not tested.
         # ('Vicon Motion Systems', ['pyCGM2 lower limb CGM24 Walking01.c3d', 'TableTennis.c3d']),
        ]


if __name__ == '__main__':
    unittest.main()
