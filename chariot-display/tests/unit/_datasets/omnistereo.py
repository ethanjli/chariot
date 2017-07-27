#!/usr/bin/env python2
import unittest
import os

from datasets import omnistereo

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

DATASETS_PATH = os.path.join(_PACKAGE_PATH, 'datasets')

class TestDataset(unittest.TestCase):
    def setUp(self):
        self.dataset = omnistereo.Dataset('omnistereo', parent_path=DATASETS_PATH)

    def test_init(self):
        print(self.dataset.parent_path)
        print(DATASETS_PATH)
        self.assertEqual(self.dataset.parent_path, DATASETS_PATH,
                         'Incorrect parent path')

    def test_point_cloud_raw_files_sequence(self):
        sequence = self.dataset.sequences['point_cloud']['raw']['files']
        self.assertEqual(sequence.file_name('000001'), 'P_hor_000001.mat',
                         'Incorrect file name')
        self.assertEqual(sequence.file_path('000001'),
                         os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Stereo_Disp',
                                      'P_hor_000001.mat'),
                         'Incorrect file path')
        self.assertEqual(list(sequence.indices), ['000001', '000002', '000003'],
                         'Incorrect indices')

