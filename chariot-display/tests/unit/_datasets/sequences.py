#!/usr/bin/env python2
import unittest
import os

from datasets import sequences

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

SEQUENCE_PARENT_PATH = os.path.join(_PACKAGE_PATH, 'sequence')

class TextFileSequence(sequences.FileSequence):
    def __init__(self, *args, **kwargs):
        super(TextFileSequence, self).__init__(*args, **kwargs)

    def __getitem__(self, index):
        with open(self.file_path(index), 'r') as f:
            return f.read().replace('\n', '').strip()

class TestFileSequence(unittest.TestCase):
    def setUp(self):
        self.sequence = TextFileSequence(SEQUENCE_PARENT_PATH, suffix='.txt')

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

    def test_loading(self):
        self.assertEqual(self.sequence['0001'], 'foo',
                         'Incorrect loading')
        self.assertEqual(self.sequence['0002'], 'bar',
                         'Incorrect loading')
        self.assertEqual(self.sequence['0003'], 'foobar',
                         'Incorrect loading')

class TestFileSequenceLoader(unittest.TestCase):
    def setUp(self):
        self.sequence = TextFileSequence(SEQUENCE_PARENT_PATH, suffix='.txt')
        self.loader = sequences.FileSequenceLoader(self.sequence)
        self.loader.load()

    def test_load_next(self):
        contents = self.loader.load_next()
        self.assertEqual(contents, 'foo',
                         'Incorrect loading')
        contents = self.loader.load_next()
        self.assertEqual(contents, 'bar',
                         'Incorrect loading')
        contents = self.loader.load_next()
        self.assertEqual(contents, 'foobar',
                         'Incorrect loading')
        contents = self.loader.load_next()
        self.assertIsNone(contents,
                          'Incorrect loading sentinel value')

    def test_next(self):
        contents = next(self.loader)
        self.assertEqual(contents, 'foo',
                         'Incorrect loading')
        contents = next(self.loader)
        self.assertEqual(contents, 'bar',
                         'Incorrect loading')
        contents = next(self.loader)
        self.assertEqual(contents, 'foobar',
                         'Incorrect loading')
        try:
            contents = next(self.loader)
            self.assertFalse(True,
                             'Incorrect generator termination behavior.')
        except StopIteration:
            pass

    def test_reset(self):
        self.test_load_next()
        self.loader.reset()
        self.test_load_next()
        self.loader.reset()
        self.test_next()
        self.loader.reset()
        self.test_next()

class TestFileSequenceConcurrentLoader(unittest.TestCase):
    def setUp(self):
        self.sequence = TextFileSequence(SEQUENCE_PARENT_PATH, suffix='.txt')

    def parallelsafe_setUp(self):
        self.loader = sequences.FileSequenceConcurrentLoader(self.sequence, 2)
        self.loader.load()

    def test_next(self):
        self.parallelsafe_setUp()
        contents = next(self.loader)
        self.assertEqual(contents, 'foo',
                         'Incorrect loading')
        contents = next(self.loader)
        self.assertEqual(contents, 'bar',
                         'Incorrect loading')
        contents = next(self.loader)
        self.assertEqual(contents, 'foobar',
                         'Incorrect loading')
        try:
            contents = next(self.loader)
            self.assertFalse(True,
                             'Incorrect generator termination behavior.')
        except StopIteration:
            pass

    def test_reset(self):
        self.parallelsafe_setUp()
        self.loader.load()
        self.test_next()
        self.loader.reset()
        self.loader.load()
        self.test_next()
        self.loader.reset()
        self.loader.load()
        self.test_next()
        self.loader.reset()
        self.loader.load()
        self.test_next()

    def tearDown(self):
        self.loader.stop_loading()

