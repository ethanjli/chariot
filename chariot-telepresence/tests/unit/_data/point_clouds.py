#!/usr/bin/env python2
import unittest
import os

from data import point_clouds

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

POINT_CLOUD_MAT_PATH = os.path.join(_PACKAGE_PATH, 'point_cloud.mat')

class TestLoading(unittest.TestCase):
    def setUp(self):
        self.point_cloud = point_clouds.PointCloud()
        self.point_cloud.load_from_mat(POINT_CLOUD_MAT_PATH)

    def test_shape(self):
        self.assertEqual(self.point_cloud.points.shape, self.point_cloud.colors.shape,
                         'Self-inconsistent point cloud shape')
        self.assertEqual(self.point_cloud.points.shape, (290286, 3),
                         'Incorrect point cloud shape')
        self.assertEqual(self.point_cloud.colors.shape, (290286, 3),
                         'Incorrect point cloud shape')

    def test_num_points(self):
        self.assertEqual(self.point_cloud.num_points, 290286,
                         'Incorrect number of points in point cloud')

