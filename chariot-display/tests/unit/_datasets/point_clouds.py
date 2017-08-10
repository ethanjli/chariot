#!/usr/bin/env python2
import unittest
import os

from data.point_clouds import ParallelLoader
from datasets.point_clouds import Sequence, SequenceLoader, SequenceConcurrentLoader

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

DATASETS_PATH = os.path.join(_PACKAGE_PATH, 'datasets')

class TestSequence(unittest.TestCase):
    def setUp(self):
        self.omnistereo_sequence = Sequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_', array_name='S', transpose=True
        )
        self.video_popup_sequence_sparse = Sequence(
            os.path.join(DATASETS_PATH, 'video_popup'), 'points_sparse_'
        )
        self.video_popup_sequence_dense = Sequence(
            os.path.join(DATASETS_PATH, 'video_popup'), 'points_dense_nearest_'
        )

    def test_getitem(self):
        self.assertEqual(self.omnistereo_sequence['000001'].num_points, 292576,
                         'Incorrect point cloud loading')
        self.assertEqual(self.omnistereo_sequence['000002'].num_points, 292766,
                         'Incorrect point cloud loading')
        self.assertEqual(self.omnistereo_sequence['000003'].num_points, 293242,
                         'Incorrect point cloud loading')
        for i in range(3):
            self.assertEqual(self.video_popup_sequence_sparse[str(i)].num_points, 7195,
                             'Incorrect point cloud loading')
            self.assertEqual(self.video_popup_sequence_dense[str(i)].num_points, 453620,
                             'Incorrect point cloud loading')

    def test_num_points(self):
        self.assertEqual(self.omnistereo_sequence.num_points, 292576,
                         'Incorrect num points')

    def test_num_samples(self):
        self.assertEqual(self.omnistereo_sequence.num_samples, 3,
                         'Incorrect num samples')

class TestSequenceLoader(unittest.TestCase):
    def setUp(self):
        self.omnistereo_sequence = Sequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_', array_name='S', transpose=True
        )
        self.video_popup_sequence = Sequence(
            os.path.join(DATASETS_PATH, 'video_popup'), 'points_sparse_'
        )
        self.omnistereo_loader = SequenceLoader(self.omnistereo_sequence)
        self.omnistereo_loader.load()
        self.video_popup_loader = SequenceLoader(self.video_popup_sequence)
        self.video_popup_loader.load()

    def test_loading(self):
        self.assertEqual(next(self.omnistereo_loader).num_points, 292576,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.omnistereo_loader).num_points, 292766,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.omnistereo_loader).num_points, 293242,
                         'Incorrect point cloud loading')
        for i in range(3):
            self.assertEqual(next(self.video_popup_loader).num_points, 7195,
                             'Incorrect point cloud loading')

class TestSequenceConcurrentLoader(unittest.TestCase):
    def setUp(self):
        self.omnistereo_sequence = Sequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_', array_name='S', transpose=True
        )
        self.video_popup_sequence = Sequence(
            os.path.join(DATASETS_PATH, 'video_popup'), 'points_sparse_'
        )
        self.omnistereo_loader = SequenceConcurrentLoader(self.omnistereo_sequence)
        self.omnistereo_loader.load()
        self.video_popup_loader = SequenceLoader(self.video_popup_sequence)
        self.video_popup_loader.load()

    def test_loading(self):
        self.assertEqual(next(self.omnistereo_loader).num_points, 292576,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.omnistereo_loader).num_points, 292766,
                         'Incorrect point cloud loading')
        self.assertEqual(next(self.omnistereo_loader).num_points, 293242,
                         'Incorrect point cloud loading')
        for i in range(3):
            self.assertEqual(next(self.video_popup_loader).num_points, 7195,
                             'Incorrect point cloud loading')

    def tearDown(self):
        self.omnistereo_loader.stop_loading()
        self.video_popup_loader.stop_loading()

class TestSequenceParallelLoader(unittest.TestCase):
    def setUp(self):
        self.omnistereo_sequence = Sequence(
            os.path.join(DATASETS_PATH, 'omnistereo', 'Seq_0008', 'Rectification'),
            'point_cloud_stereo_', array_name='S', transpose=True
        )
        self.video_popup_sequence = Sequence(
            os.path.join(DATASETS_PATH, 'video_popup'), 'points_sparse_'
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
            lambda: SequenceLoader(self.omnistereo_sequence, 300000))
        self.loader.load()
        self.assert_generation()

    def test_loading_with_concurrency(self):
        self.loader = ParallelLoader(
            lambda: SequenceConcurrentLoader(self.omnistereo_sequence, max_num_points=300000))
        self.loader.load()
        self.assert_generation()

    def tearDown(self):
        if self.loader is not None:
            self.loader.stop_loading()

