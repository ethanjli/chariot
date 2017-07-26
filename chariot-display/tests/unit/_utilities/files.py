#!/usr/bin/env python2
import unittest
import os

from utilities import files

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

SEQUENCE_PARENT_PATH = os.path.join(_PACKAGE_PATH, 'sequence')

class TestPaths(unittest.TestCase):
    def test_single_directory(self):
        paths = files.paths('foo', ['a', 'b', 'c'], file_suffix='.bar')
        self.assertEqual(list(paths), ['foo/a.bar', 'foo/b.bar', 'foo/c.bar'],
                         'Incorrect paths')

    def test_number_names(self):
        paths = files.paths('foo', [1, 2, 3], file_suffix='.bar')
        self.assertEqual(list(paths), ['foo/1.bar', 'foo/2.bar', 'foo/3.bar'],
                         'Incorrect paths')

    def test_multiple_directories(self):
        paths = files.paths(['foo', 'foobar'], ['a', 'b', 'c'], file_suffix='.bar')
        self.assertEqual(list(paths), [('foo/a.bar', 'foobar/a.bar'),
                                       ('foo/b.bar', 'foobar/b.bar'),
                                       ('foo/c.bar', 'foobar/c.bar')],
                         'Incorrect paths')
        paths = files.paths(['foobar', 'foo'], ['a', 'b', 'c'], file_suffix='.bar')
        self.assertEqual(list(paths), [('foobar/a.bar', 'foo/a.bar'),
                                       ('foobar/b.bar', 'foo/b.bar'),
                                       ('foobar/c.bar', 'foo/c.bar')],
                         'Incorrect paths')

class TestFiles(unittest.TestCase):
    def test_uniform(self):
        listed_files = files.file_names(SEQUENCE_PARENT_PATH, 'a', '.txt')
        self.assertEqual(list(listed_files), ['a0001.txt', 'a0002.txt', 'a0003.txt'])

    def test_nonuniform(self):
        listed_files = files.file_names(SEQUENCE_PARENT_PATH, 'b', '.txt')
        self.assertEqual(list(listed_files), ['b0.txt', 'b1.txt', 'b2.txt', 'b10.txt', 'b11.txt'])

class TestFileIndices(unittest.TestCase):
    def test_uniform(self):
        listed_files = files.file_name_roots(SEQUENCE_PARENT_PATH, 'a', '.txt')
        self.assertEqual(list(listed_files), ['0001', '0002', '0003'])

    def test_nonuniform(self):
        listed_files = files.file_name_roots(SEQUENCE_PARENT_PATH, 'b', '.txt')
        self.assertEqual(list(listed_files), ['0', '1', '2', '10', '11'])

