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


