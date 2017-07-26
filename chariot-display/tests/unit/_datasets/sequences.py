#!/usr/bin/env python2
import unittest
import os

from datasets import sequences

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

SEQUENCE_PARENT_PATH = os.path.join(_PACKAGE_PATH, 'sequence')

class TestFileSequence(unittest.TestCase):
    def setUp(self):
        self.sequence = sequences.FileSequence(SEQUENCE_PARENT_PATH, suffix='.txt')

    def test_basic(self):
        self.assertEqual(self.sequence.file_name('0001'), '0001.txt',
                         'Incorrect file path')
        self.assertEqual(self.sequence.file_path('0001'),
                         os.path.join(SEQUENCE_PARENT_PATH, '0001.txt'),
                         'Incorrect file path')

    def test_indices(self):
        self.assertEqual(list(self.sequence.indices), ['0001', '0002', '0003'],
                         'Incorrect file indices')

    def test_file_paths(self):
        self.assertEqual(list(self.sequence.file_paths),
                         [os.path.join(SEQUENCE_PARENT_PATH, '0001.txt'),
                          os.path.join(SEQUENCE_PARENT_PATH, '0002.txt'),
                          os.path.join(SEQUENCE_PARENT_PATH, '0003.txt')],
                         'Incorrect file paths')

