#!/usr/bin/env python2
import unittest
import os

from datasets import video_popup

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

DATASETS_PATH = os.path.join(_PACKAGE_PATH, 'datasets')

class TestDataset(unittest.TestCase):
    def setUp(self):
        self.dataset = video_popup.Dataset('video_popup', parent_path=DATASETS_PATH)

    def test_init(self):
        self.assertEqual(self.dataset.parent_path, DATASETS_PATH,
                         'Incorrect parent path')

    def test_point_cloud_sparse_files_sequence(self):
        sequence = self.dataset.sequences['point_cloud']['sparse']['files']
        self.assertEqual(sequence.file_name('0'), 'points_sparse_0.mat',
                         'Incorrect file name')
        self.assertEqual(sequence.file_path('0'),
                         os.path.join(DATASETS_PATH, 'video_popup',
                                      'points_sparse_0.mat'),
                         'Incorrect file path')
        self.assertEqual(list(sequence.indices), ['0', '1', '2'],
                         'Incorrect indices')

    def test_point_cloud_dense_nearest_files_sequence(self):
        sequence = self.dataset.sequences['point_cloud']['dense_nearest']['files']
        self.assertEqual(sequence.file_name('0'), 'points_dense_nearest_0.mat',
                         'Incorrect file name')
        self.assertEqual(sequence.file_path('0'),
                         os.path.join(DATASETS_PATH, 'video_popup',
                                      'points_dense_nearest_0.mat'),
                         'Incorrect file path')
        self.assertEqual(list(sequence.indices), ['0', '1', '2'],
                         'Incorrect indices')

    def test_point_cloud_dense_linear_files_sequence(self):
        sequence = self.dataset.sequences['point_cloud']['dense_linear']['files']
        self.assertEqual(sequence.file_name('0'), 'points_dense_linear_0.mat',
                         'Incorrect file name')
        self.assertEqual(sequence.file_path('0'),
                         os.path.join(DATASETS_PATH, 'video_popup',
                                      'points_dense_linear_0.mat'),
                         'Incorrect file path')
        self.assertEqual(list(sequence.indices), ['0', '1', '2'],
                         'Incorrect indices')

