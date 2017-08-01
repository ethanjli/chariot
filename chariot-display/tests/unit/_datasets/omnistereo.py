#!/usr/bin/env python2
import unittest
import os

from data import point_clouds
from datasets import omnistereo

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

DATASETS_PATH = os.path.join(_PACKAGE_PATH, 'datasets')

class TestPointCloudSequence(unittest.TestCase):
    def setUp(self):
        self.sequence = omnistereo.PointCloudSequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_'
        )

    def test_getitem(self):
        self.assertEqual(self.sequence['000001'].num_points, 292576,
                         'Incorrect point cloud loading')
        self.assertEqual(self.sequence['000002'].num_points, 292766,
                         'Incorrect point cloud loading')
        self.assertEqual(self.sequence['000003'].num_points, 293242,
                         'Incorrect point cloud loading')

    def test_num_points(self):
        self.assertEqual(self.sequence.num_points, 292576,
                         'Incorrect num points')

    def test_num_samples(self):
        self.assertEqual(self.sequence.num_samples, 3,
                         'Incorrect num samples')

class TestPointCloudSequenceLoader(unittest.TestCase):
    def setUp(self):
        self.sequence = omnistereo.PointCloudSequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_'
        )
        self.loader = omnistereo.PointCloudSequenceLoader(self.sequence)
        self.loader.load()

    def test_loading(self):
        self.assertEqual(next(self.loader).num_points, 292576,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.loader).num_points, 292766,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.loader).num_points, 293242,
                         'Incorrect point cloud loading')

class TestPointCloudSequenceConcurrentLoader(unittest.TestCase):
    def setUp(self):
        self.sequence = omnistereo.PointCloudSequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_'
        )
        self.loader = omnistereo.PointCloudSequenceConcurrentLoader(self.sequence)
        self.loader.load()

    def test_loading(self):
        self.assertEqual(next(self.loader).num_points, 292576,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.loader).num_points, 292766,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.loader).num_points, 293242,
                         'Incorrect point cloud loading')

    def tearDown(self):
        self.loader.stop_loading()

class TestPointCloudSequenceParallelLoader(unittest.TestCase):
    def setUp(self):
        self.sequence = omnistereo.PointCloudSequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_'
        )
        self.loader = None

    def assert_generation(self):
        self.assertEqual(next(self.loader).num_points, 292576,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.loader).num_points, 292766,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.loader).num_points, 293242,
                         'Incorrect point cloud loading')

    def test_loading(self):
        self.loader = point_clouds.ParallelLoader(
            lambda: omnistereo.PointCloudSequenceLoader(self.sequence, 300000))
        self.loader.load()
        self.assert_generation()

    def test_loading_with_concurrency(self):
        self.loader = point_clouds.ParallelLoader(
            lambda: omnistereo.PointCloudSequenceConcurrentLoader(
                self.sequence, max_num_points=300000))
        self.loader.load()
        self.assert_generation()

    def tearDown(self):
        if self.loader is not None:
            self.loader.stop_loading()

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
        self.assertEqual(sequence.file_name('000001'), 'point_cloud_stereo_000001.mat',
                         'Incorrect file name')
        self.assertEqual(sequence.file_path('000001'),
                         os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification',
                                      'point_cloud_stereo_000001.mat'),
                         'Incorrect file path')
        self.assertEqual(list(sequence.indices), ['000001', '000002', '000003'],
                         'Incorrect indices')

