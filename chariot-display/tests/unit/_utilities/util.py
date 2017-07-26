#!/usr/bin/env python2
import unittest

import numpy as np

from utilities import util

class TestGetFromTree(unittest.TestCase):
    def setUp(self):
        self.tree = {
            'foo': 42,
            'bar': {
                'foobar': 12345
            }
        }

    def test_special(self):
        self.assertEqual(util.get_from_tree(self.tree, []), self.tree,
                         'Incorrect empty key lookup')
        self.assertEqual(util.get_from_tree(self.tree, 'foo'), 42,
                         'Incorrect string key lookup')

    def test_paths(self):
        self.assertEqual(util.get_from_tree(self.tree, ['bar']), self.tree['bar'],
                         'Incorrect string key lookup')
        self.assertEqual(util.get_from_tree(self.tree, ['bar', 'foobar']), 12345,
                         'Incorrect string key lookup')

    def test_iterable(self):
        path = ['bar', 'foobar']
        self.assertEqual(util.get_from_tree(self.tree, iter(path)), 12345,
                         'Incorrect string key lookup')

class TestRingBuffer(unittest.TestCase):
    def setUp(self):
        self.ringBuffer = util.RingBuffer(4)

    def test_initial(self):
        self.assertEqual(self.ringBuffer.head, None,
                         'Incorrect initial head')
        self.assertEqual(self.ringBuffer.tail, None,
                         'Incorrect initial tail')
        self.assertEqual(self.ringBuffer.data.size, 4,
                         'Incorrect initial buffer')
        self.assertEqual(self.ringBuffer.continuous.size, 0,
                         'Incorrect initial continuous view')
        self.assertEqual(self.ringBuffer.length, 0,
                         'Incorrect initial length')

    def test_reset(self):
        for i in range(10):
            self.ringBuffer.append(i)
            self.ringBuffer.reset()
            self.test_initial()

    def test_append(self):
        self.ringBuffer.append(1)
        self.assertEqual(self.ringBuffer.head, 1,
                         'Incorrect head')
        self.assertEqual(self.ringBuffer.tail, 1,
                         'Incorrect tail')
        self.assertEqual(self.ringBuffer.continuous.size, 1,
                         'Incorrect continuous view')
        self.assertEqual(self.ringBuffer.length, 1,
                         'Incorrect length')

        self.ringBuffer.append(2)
        self.assertEqual(self.ringBuffer.head, 2,
                         'Incorrect head')
        self.assertEqual(self.ringBuffer.tail, 1,
                         'Incorrect tail')
        self.assertEqual(self.ringBuffer.continuous.size, 2,
                         'Incorrect continuous view')
        self.assertEqual(self.ringBuffer.length, 2,
                         'Incorrect length')

        self.ringBuffer.append(3)
        self.assertEqual(self.ringBuffer.head, 3,
                         'Incorrect head')
        self.assertEqual(self.ringBuffer.tail, 1,
                         'Incorrect tail')
        self.assertEqual(self.ringBuffer.continuous.size, 3,
                         'Incorrect continuous view')
        self.assertEqual(self.ringBuffer.length, 3,
                         'Incorrect length')

        for i in range(4, 10):
            self.ringBuffer.append(i)
            self.assertEqual(self.ringBuffer.head, i,
                             'Incorrect head')
            self.assertEqual(self.ringBuffer.tail, i - 3,
                             'Incorrect tail')
            self.assertEqual(self.ringBuffer.continuous.size, 4,
                             'Incorrect continuous view')
            self.assertEqual(self.ringBuffer.continuous[0], i - 3,
                             'Incorrect continuous view')
            self.assertEqual(self.ringBuffer.continuous[1], i - 2,
                             'Incorrect continuous view')
            self.assertEqual(self.ringBuffer.continuous[2], i - 1,
                             'Incorrect continuous view')
            self.assertEqual(self.ringBuffer.continuous[3], i,
                             'Incorrect continuous view')
            self.assertEqual(self.ringBuffer.length, 4,
                             'Incorrect length')

class TestGridDataToListData(unittest.TestCase):
    def test_flat(self):
        as_grid = np.array([[[1], [2], [3]], [[4], [5], [6]]])
        as_list = np.array([[1], [2], [3], [4], [5], [6]])
        self.assertEqual(
            util.grid_data_to_list_data(as_grid).tolist(), as_list.tolist(),
            'Incorrect reshape of flat grid'
        )

    def test_three_channel(self):
        as_grid = np.array([[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                            [[10, 11, 12], [13, 14, 15], [16, 17, 18]]])
        as_list = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9],
                            [10, 11, 12], [13, 14, 15], [16, 17, 18]])
        self.assertEqual(
            util.grid_data_to_list_data(as_grid).tolist(), as_list.tolist(),
            'Incorrect reshape of flat grid'
        )

class TestUpdateListDataBuffer(unittest.TestCase):
    def setUp(self):
        self.small_buffer = np.zeros((5, 3))
        self.large_buffer = np.zeros((10, 3))
        self.list = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9],
                              [10, 11, 12], [13, 14, 15], [16, 17, 18]])
        self.tiny_list = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9],
                                   [0, 0, 0], [0, 0, 0]])
        self.small_list = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9],
                                    [10, 11, 12], [13, 14, 15]])
        self.large_list = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9],
                                    [10, 11, 12], [13, 14, 15], [16, 17, 18],
                                    [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_update(self):
        for i in range(20):
            util.update_list_data_buffer(self.small_buffer, self.small_list, i)
            self.assertEqual(
                self.small_buffer.tolist(), self.small_list.tolist(),
                'Incorrect update of small buffer with larger list'
            )

    def test_oversized_update(self):
        for i in range(20):
            util.update_list_data_buffer(self.small_buffer, self.list, i)
            self.assertEqual(
                self.small_buffer.tolist(), self.small_list.tolist(),
                'Incorrect update of small buffer with larger list'
            )

    def test_undersized_update(self):
        for i in range(20):
            util.update_list_data_buffer(self.large_buffer, self.list, i)
            self.assertEqual(
                self.large_buffer.tolist(), self.large_list.tolist(),
                'Incorrect update of small buffer with larger list'
            )

    def test_downsized_update(self):
        util.update_list_data_buffer(self.small_buffer, self.small_list, 5)
        util.update_list_data_buffer(self.small_buffer, self.small_list[:3, :], 5)
        self.assertEqual(
            self.small_buffer.tolist(), self.tiny_list.tolist(),
            'Incorrect update of small buffer with larger list'
        )

    def test_downsized_update_parsimony(self):
        util.update_list_data_buffer(self.small_buffer, self.small_list, 5)
        util.update_list_data_buffer(self.small_buffer, self.small_list[:3, :], 3)
        self.assertEqual(
            self.small_buffer.tolist(), self.small_list.tolist(),
            'Incorrect update of small buffer with larger list'
        )

class TestTimeRange(unittest.TestCase):
    def test_init(self):
        time_range = util.TimeRange()
        self.assertEqual(time_range.start, None,
                         'Incorrect initialization')
        self.assertEqual(time_range.end, None,
                         'Incorrect initialization')
        self.assertEqual(time_range.reference, None,
                         'Incorrect initialization')
        self.assertFalse(time_range.referenced,
                         'Incorrect initialization')

        time_range = util.TimeRange(100, 200, 0)
        self.assertEqual(time_range.start, 100,
                         'Incorrect initialization')
        self.assertEqual(time_range.end, 200,
                         'Incorrect initialization')
        self.assertEqual(time_range.reference, 0,
                         'Incorrect initialization')
        self.assertTrue(time_range.referenced,
                        'Incorrect initialization')

        time_range = util.TimeRange(100, 200, duration=100)
        self.assertEqual(time_range.start, 100,
                         'Incorrect initialization')
        self.assertEqual(time_range.end, 200,
                         'Incorrect initialization')

        time_range = util.TimeRange(start=100, duration=100)
        self.assertEqual(time_range.start, 100,
                         'Incorrect initialization')
        self.assertEqual(time_range.end, 200,
                         'Incorrect initialization')

        time_range = util.TimeRange(end=200, duration=100)
        self.assertEqual(time_range.start, 100,
                         'Incorrect initialization')
        self.assertEqual(time_range.end, 200,
                         'Incorrect initialization')

    def test_reference(self):
        time_range = util.TimeRange(100, 200, 0)
        self.assertEqual(time_range.absolute, (100, 200),
                         'Incorrect zero reference')
        time_range = util.TimeRange(100, 200, 100)
        self.assertEqual(time_range.absolute, (200, 300),
                         'Incorrect nonzero reference')

    def test_duration(self):
        time_range = util.TimeRange(100, 200)
        self.assertEqual(time_range.duration, 100,
                         'Incorrect duration')
        time_range = util.TimeRange(100, 200, 100)
        self.assertEqual(time_range.duration, 100,
                         'Incorrect duration with reference')

class TestNaturalSorting(unittest.TestCase):
    def setUp(self):
        self.strings = [
            '4',
            'c',
            'a',
            '0',
            '0003',
            '2',
            '0001',
            'b'
        ]
        self.sorted_strings = [
            '0',
            '0001',
            '2',
            '0003',
            '4',
            'a',
            'b',
            'c'
        ]

    def test_sort(self):
        self.assertEqual(sorted(self.strings, key=util.natural_keys), self.sorted_strings,
                         'Incorrect natural sorting')

