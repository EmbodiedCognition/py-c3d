import unittest
import numpy as np
import warnings
import os
from test.zipload import Zipload, TEMP

from scripts.c3d2csv import convert


class Script_c3d2csv_Test(unittest.TestCase):

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
             #('Vicon Motion Systems', ['pyCGM2 lower limb CGM24 Walking01.c3d', 'TableTennis.c3d']),
            ]

    def setUp(self):
        Zipload.download()
        Zipload.extract('sample01.zip')

    class Args:
        include_error = False
        include_camera = False
        include_analog = False

    def test_a_convert(self):
        for subdir, files in self.zip_files:
            for file in files:
                file_path = os.path.join(TEMP, 'sample00.zip', subdir, file)
                convert(file_path, Script_c3d2csv_Test.Args(), '\t', '\n')
