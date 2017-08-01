#!/usr/bin/env python2
import unittest
import sys
import time
import ctypes
import os

import numpy as np

from utilities import util, parallelism
from data import data, arrays, point_clouds

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

def make_point_cloud(num_points, i):
    return [
        np.array([[n * i, n * i + 1, n * i + 2]
                  for n in range(num_points)]).astype(int),
        np.array([[n * (i + 1), n * (i + 2)]
                  for n in range(num_points)]).astype(float)
    ]

class PointCloudDoubleBufferClient(parallelism.DoubleBufferedProcess):
    def __init__(self, *args, **kwargs):
        super(PointCloudDoubleBufferClient, self).__init__(
            point_clouds.DoubleBuffer, 1, 1)
        self.double_buffer.initialize((ctypes.c_int, ctypes.c_double), ((4, 3), (4, 2)))

    # From Process

    def on_run_start(self):
        self.send_output('started')

    def execute(self, next_input):
        if next_input[0] == 'write':
            time.sleep(0.05)
            self.write_to_buffer((next_input[1],
                                  make_point_cloud(next_input[1], next_input[2])))
        elif next_input[0] == 'read':
            self.send_output({
                'num_points': self.read_buffer.num_points.value,
                'properties': self.read_buffer.point_properties
            })
        elif next_input[0] == 'swap':
            self.swap_buffers()
            self.send_output('swap')

    def on_run_parent_start(self):
        parallelism.acquire_lock_poll(self.double_buffer.read_lock, block=True, timeout=1)

    # From DoubleBufferedProcess

    def on_write_to_buffer(self, write_data, write_buffer):
        write_buffer.num_points.value = write_data[0]
        for (dest, source) in zip(write_buffer.point_properties, write_data[1]):
            util.update_list_data_buffer(dest, source)

class TestPointCloudDoubleBuffer(unittest.TestCase):
    def parallelsafe_setUp(self):
        self.process = PointCloudDoubleBufferClient()
        self.process.run_parallel()
        self.assertEqual(self.process.receive_output(), 'started',
                         'Incorrect initialization')

    def assert_read_buffer_consistency(self):
        read_result = self.round_trip('read')
        self.assertEqual(self.process.read_buffer.num_points.value, read_result['num_points'],
                         'Double buffer inconsistency')
        for (parent_array, child_array) in zip(
                self.process.read_buffer.point_properties,
                read_result['properties']):
            self.assertEqual(parent_array.tolist(), child_array.tolist(),
                             'Double buffer inconsistency')

    def round_trip(self, *input_args):
        self.process.send_input(input_args)
        return self.process.receive_output()

    def assert_result(self, num_points, i, buffer_size=4):
        read_result = self.round_trip('read')
        self.assertEqual(read_result['num_points'], num_points,
                         'Read/write inconsistency')
        properties = make_point_cloud(num_points, i)
        if num_points > buffer_size:
            properties = (array[:buffer_size] for array in properties)
        elif num_points < buffer_size:
            padding_height = buffer_size - num_points
            properties = [np.concatenate([array, np.zeros((padding_height,
                                                           array.shape[1])).astype(int)],
                                         axis=0)
                          for array in properties]
        for (reference_array, child_array) in zip(properties, read_result['properties']):
            self.assertEqual(child_array.tolist(), reference_array.tolist(),
                             'Point properties inconsistency')

    def test_child_writes(self):
        self.parallelsafe_setUp()
        self.process.send_input(('write', 1, 1))
        self.process.swap_buffers()
        self.assert_result(1, 1)
        self.assert_read_buffer_consistency()
        sys.stdout.write('child[')
        for i in range(1, 8):
            for num_points in range(1, 8):
                self.process.send_input(('write', num_points, i))
                self.process.swap_buffers()
                self.assert_result(num_points, i)
                self.assert_read_buffer_consistency()
                sys.stdout.write('.')
        print(']')

    def test_parent_writes(self):
        self.parallelsafe_setUp()
        self.process.write_to_buffer((1, make_point_cloud(1, 1)))
        self.round_trip('swap')
        self.assert_result(1, 1)
        self.assert_read_buffer_consistency()
        sys.stdout.write('child[')
        for i in range(1, 8):
            for num_points in range(1, 8):
                self.process.write_to_buffer((num_points, make_point_cloud(num_points, i)))
                self.round_trip('swap')
                self.assert_result(num_points, i)
                self.assert_read_buffer_consistency()
        print(']')

    def tearDown(self):
        if self.process.process_running:
            self.process.terminate()

class PointCloudLoader(data.DataLoader, data.DataGenerator, arrays.ArraysSource):
    def __init__(self, num_points_limit, i_limit):
        self.i = 0
        self.num_points = int(0.25 * num_points_limit)
        self.num_points_limit = num_points_limit
        self.i_limit = i_limit

    # From DataGenerator

    def next(self):
        if self.num_points >= self.num_points_limit:
            raise StopIteration
        properties = make_point_cloud(self.num_points, self.i)
        self.i += 1
        if self.i >= self.i_limit:
            self.i = 0
            self.num_points += 1
        point_cloud = point_clouds.PointCloud()
        (point_cloud.points, point_cloud.colors) = properties
        return point_cloud

    def reset(self):
        self.i = 0
        self.num_points = int(0.25 * self.num_points_limit)

    # From ArraysSource

    @property
    def array_ctypes(self):
        return (ctypes.c_int, ctypes.c_double)

    @property
    def array_shapes(self):
        num_points = int(0.75 * self.num_points_limit)
        return ((num_points, 3), (num_points, 2))

class TestPointCloudParallelLoader(unittest.TestCase):
    def setUp(self):
        self.loader = None

    def test_generation(self):
        self.loader = point_clouds.ParallelLoader(lambda: PointCloudLoader(10, 5))
        for _ in range(5):
            self.loader.load()
            for num_points in range(int(0.25 * 10), 10):
                for i in range(5):
                    point_cloud = point_clouds.PointCloud()
                    properties = make_point_cloud(num_points, i)
                    num_allowed_points = min(num_points, int(0.75 * 10))
                    point_cloud.points = properties[0][:num_allowed_points]
                    point_cloud.colors = properties[1][:num_allowed_points]
                    result = next(self.loader)
                    self.assertEqual(result.points.tolist(), point_cloud.points.tolist(),
                                     'Incorrect point generation')
                    self.assertEqual(result.colors.tolist(), point_cloud.colors.tolist(),
                                     'Incorrect color generation')
            try:
                print(next(self.loader))
                self.assertFalse(True, 'Incorrect stopping behavior')
            except StopIteration:
                pass
            self.loader.stop_loading()
            self.loader.reset()

    def tearDown(self):
        if self.loader is not None:
            self.loader.stop_loading()

