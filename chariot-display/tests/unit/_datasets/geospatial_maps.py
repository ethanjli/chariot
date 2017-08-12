#!/usr/bin/env python2
import unittest
import os

from datasets import geospatial_maps

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))
DATASETS_PATH = os.path.join(_PACKAGE_PATH, 'datasets')
STANFORD_DATASET_PATH = os.path.join(DATASETS_PATH, 'geospatial_maps')

class TestDataset(unittest.TestCase):
    def setUp(self):
        self.dataset = geospatial_maps.Dataset('geospatial_maps', parent_path=DATASETS_PATH)

    def test_init(self):
        self.assertEqual(self.dataset.get_path('roads'),
                         os.path.join(DATASETS_PATH, 'geospatial_maps', 'shape', 'roads.shp'),
                         'Incorrect path')
        self.assertEqual(self.dataset.get_path('buildings'),
                         os.path.join(DATASETS_PATH, 'geospatial_maps', 'shape', 'buildings.shp'),
                         'Incorrect path')

    def test_bounds(self):
        self.assertEqual(self.dataset.bounds, (-122.18383, -122.15447, 37.42149, 37.43545),
                         'Incorrect bounds')

