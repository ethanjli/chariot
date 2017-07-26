#!/usr/bin/env python2
import unittest

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

