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
        self.assertIsNone(self.ringBuffer.head,
                          'Incorrect initial head')
        self.assertIsNone(self.ringBuffer.tail,
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
        self.assertIsNone(time_range.start,
                          'Incorrect initialization')
        self.assertIsNone(time_range.end,
                          'Incorrect initialization')
        self.assertIsNone(time_range.reference,
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
            '10',
            '11',
            '013',
            '21',
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
            '10',
            '11',
            '013',
            '21',
            'a',
            'b',
            'c'
        ]

    def test_sort(self):
        self.assertEqual(sorted(self.strings, key=util.natural_keys), self.sorted_strings,
                         'Incorrect natural sorting')

class TestSequence(unittest.TestCase):
    def setUp(self):
        self.string = 'abcdefghijklmnopqrstuvwxyz'
        self.list = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

    def test_string_sequence(self):
        sequence = util.sequence(self.string)
        self.assertEqual(list(sequence), [char for char in self.string],
                         'Incorrect sequence')
        sequence = util.sequence(self.string, range(5, 10))
        self.assertEqual(list(sequence), ['f', 'g', 'h', 'i', 'j'],
                         'Incorrect indexed sequence')

    def test_list_sequence(self):
        sequence = util.sequence(self.list)
        self.assertEqual(list(sequence), self.list,
                         'Incorrect sequence')
        sequence = util.sequence(self.list, [3, 4, 5])
        self.assertEqual(list(sequence), [8, 10, 12],
                         'Incorrect indexed sequence')
        sequence = util.sequence(self.list, [5, 4, 3])
        self.assertEqual(list(sequence), [12, 10, 8],
                         'Incorrect arbitrarily-ordered indexed sequence')

class TestTimeRangeSequence(unittest.TestCase):
    def setUp(self):
        self.times = [10, 13, 14, 15, 18, 20, 22, 26, 27, 28, 29, 30, 100]

    def test_start_times(self):
        times = util.time_range_sequence(self.times)
        self.assertEqual(list(times), self.times,
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, -10)
        self.assertEqual(list(times), self.times,
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 28)
        self.assertEqual(list(times), [28, 29, 30, 100],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 90)
        self.assertEqual(list(times), [100],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 100)
        self.assertEqual(list(times), [100],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 200)
        self.assertEqual(list(times), [],
                         'Incorrect sequence')

    def test_end_times(self):
        times = util.time_range_sequence(self.times, end=100)
        self.assertEqual(list(times), self.times,
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, end=200)
        self.assertEqual(list(times), self.times,
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, end=90)
        self.assertEqual(list(times), self.times[:-1],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, end=5)
        self.assertEqual(list(times), [],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, end=0)
        self.assertEqual(list(times), [],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, end=9)
        self.assertEqual(list(times), [],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, end=10)
        self.assertEqual(list(times), [10],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, end=12)
        self.assertEqual(list(times), [10],
                         'Incorrect sequence')

    def test_start_end_times(self):
        times = util.time_range_sequence(self.times, 5, 10)
        self.assertEqual(list(times), [10],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 9, 18)
        self.assertEqual(list(times), [10, 13, 14, 15, 18],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 10, 18)
        self.assertEqual(list(times), [10, 13, 14, 15, 18],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 9, 19)
        self.assertEqual(list(times), [10, 13, 14, 15, 18],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 10, 19)
        self.assertEqual(list(times), [10, 13, 14, 15, 18],
                         'Incorrect sequence')

    def test_yield_indices(self):
        times = util.time_range_sequence(self.times, 5, 10, True)
        self.assertEqual(list(times), [(0, 10)],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 9, 18, True)
        self.assertEqual(list(times), [(0, 10), (1, 13), (2, 14), (3, 15), (4, 18)],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 10, 18, True)
        self.assertEqual(list(times), [(0, 10), (1, 13), (2, 14), (3, 15), (4, 18)],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 9, 19, True)
        self.assertEqual(list(times), [(0, 10), (1, 13), (2, 14), (3, 15), (4, 18)],
                         'Incorrect sequence')
        times = util.time_range_sequence(self.times, 10, 19, True)
        self.assertEqual(list(times), [(0, 10), (1, 13), (2, 14), (3, 15), (4, 18)],
                         'Incorrect sequence')

class TestTimeAlignedSequence(unittest.TestCase):
    def setUp(self):
        self.times = [10, 13, 14, 15, 18, 20, 22, 26, 27, 28, 29, 30, 100]

    def test_reference_before(self):
        times = util.time_aligned_sequence(self.times, [9, 11])
        self.assertEqual(list(times), [10, 13],
                         'Incorrect alignment')
        times = util.time_aligned_sequence(self.times, [9, 11, 12])
        self.assertEqual(list(times), [10, 13, 13],
                         'Incorrect alignment')

    def test_reference_after(self):
        times = util.time_aligned_sequence(self.times, [11, 12, 13, 14])
        self.assertEqual(list(times), [13, 13, 13, 14],
                         'Incorrect alignment')

    def test_reference_on(self):
        times = util.time_aligned_sequence(self.times, [10, 12, 13, 14])
        self.assertEqual(list(times), [10, 13, 13, 14],
                         'Incorrect alignment')

    def test_reference_iterator(self):
        times = util.time_aligned_sequence(self.times, iter([9, 11]))
        self.assertEqual(list(times), [10, 13],
                         'Incorrect alignment')

    def test_reference_at_end(self):
        times = util.time_aligned_sequence(self.times, [9, 14, 19, 31, 100])
        self.assertEqual(list(times), [10, 14, 20, 100, 100],
                         'Incorrect alignment')

    def test_reference_past_end(self):
        times = util.time_aligned_sequence(self.times, [9, 14, 19, 31, 100, 101])
        self.assertEqual(list(times), [10, 14, 20, 100, 100],
                         'Incorrect alignment')

    def test_references_between(self):
        times = util.time_aligned_sequence(self.times, [9, 11, 12, 13])
        self.assertEqual(list(times), [10, 13, 13, 13],
                         'Incorrect alignment')
        times = util.time_aligned_sequence(self.times, [9, 11, 12, 13, 14])
        self.assertEqual(list(times), [10, 13, 13, 13, 14],
                         'Incorrect alignment')
        times = util.time_aligned_sequence(self.times, [9, 14, 19, 31])
        self.assertEqual(list(times), [10, 14, 20, 100],
                         'Incorrect alignment')

