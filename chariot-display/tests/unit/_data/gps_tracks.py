#!/usr/bin/env python2
import unittest
import os
import datetime

from data import gps_tracks

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))
TRACK_KML_PATH = os.path.join(_PACKAGE_PATH, 'gps_track.kml')

class TestLoading(unittest.TestCase):
    def setUp(self):
        self.track = gps_tracks.Track()
        self.track.load_from_kml(TRACK_KML_PATH)

    def test_loading(self):
        self.assertEqual(len(self.track.timestamps), 116,
                         'Incorrect loading')
        self.assertEqual(len(self.track.coordinates), len(self.track.timestamps),
                         'Incorrect loading')
        self.assertTrue(isinstance(self.track.timestamps[0], datetime.datetime),
                        'Incorrect timestamp parsing')
        self.assertEqual(self.track.coordinates[0][0], -122.17424, 'Incorrect coordinate parsing')
        self.assertEqual(self.track.coordinates[0][1], 37.42786, 'Incorrect coordinate parsing')
        self.assertEqual(self.track.coordinates[0][2], -9999.0, 'Incorrect coordinate parsing')

    def test_samples(self):
        self.assertEqual(self.track.samples[0].coord[0], -122.17424, 'Incorrect coordinate parsing')
        self.assertEqual(self.track.samples[0].coord[1], 37.42786, 'Incorrect coordinate parsing')
        self.assertEqual(self.track.samples[0].coord[2], -9999.0, 'Incorrect coordinate parsing')

    def test_long_lat(self):
        self.assertEqual(self.track.longitudes[0], -122.17424, 'Incorrect coordinate parsing')
        self.assertEqual(self.track.latitudes[0], 37.42786, 'Incorrect coordinate parsing')

    def test_bounds(self):
        print self.track.bounds

class TestKMLSequence(unittest.TestCase):
    def setUp(self):
        self.sequence = gps_tracks.KMLSequence(TRACK_KML_PATH)

    def test_loading(self):
        self.sequence.load()
        next_coordinates = next(self.sequence).coord
        self.assertEqual(next_coordinates[0], -122.17424, 'Incorrect coordinate parsing')
        self.assertEqual(next_coordinates[1], 37.42786, 'Incorrect coordinate parsing')
        self.assertEqual(next_coordinates[2], -9999.0, 'Incorrect coordinate parsing')

