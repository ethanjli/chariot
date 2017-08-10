#!/usr/bin/env python2
import unittest
import os

from data.point_clouds import ParallelLoader
from datasets.point_clouds import Sequence, SequenceLoader, SequenceConcurrentLoader

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

DATASETS_PATH = os.path.join(_PACKAGE_PATH, 'datasets')

class TestSequence(unittest.TestCase):
    def setUp(self):
        self.sequence = Sequence(
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

class TestSequenceLoader(unittest.TestCase):
    def setUp(self):
        self.sequence = Sequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_'
        )
        self.loader = SequenceLoader(self.sequence)
        self.loader.load()

    def test_loading(self):
        self.assertEqual(next(self.loader).num_points, 292576,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.loader).num_points, 292766,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.loader).num_points, 293242,
                         'Incorrect point cloud loading')

class TestSequenceConcurrentLoader(unittest.TestCase):
    def setUp(self):
        self.sequence = Sequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_'
        )
        self.loader = SequenceConcurrentLoader(self.sequence)
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

class TestSequenceParallelLoader(unittest.TestCase):
    def setUp(self):
        self.sequence = Sequence(
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
        self.loader = ParallelLoader(
            lambda: SequenceLoader(self.sequence, 300000))
        self.loader.load()
        self.assert_generation()

    def test_loading_with_concurrency(self):
        self.loader = ParallelLoader(
            lambda: SequenceConcurrentLoader(self.sequence, max_num_points=300000))
        self.loader.load()
        self.assert_generation()

    def tearDown(self):
        if self.loader is not None:
            self.loader.stop_loading()

