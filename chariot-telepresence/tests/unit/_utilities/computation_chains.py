#!/usr/bin/env python2
import unittest
import os

from utilities import computation_chains

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))

POINT_CLOUD_MAT_PATH = os.path.join(_PACKAGE_PATH, 'point_cloud.mat')

class Parameter(computation_chains.Parameter):
    def __init__(self, value):
        super(Parameter, self).__init__()
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

class ParameterDoubler(computation_chains.ParameterPreprocessor):
    def __init__(self):
        super(ParameterDoubler, self).__init__()

    def preprocess(self, value):
        return 2 * value

    def unpreprocess(self, value):
        return 0.5 * value

class TestParameterChaining(unittest.TestCase):
    def setUp(self):
        self.chain = [
            Parameter(1),
            Parameter(2),
            Parameter(3)
        ]
        computation_chains.chain(*self.chain)

    def test_connectivity(self):
        self.assertEqual(self.chain[0].source, None,
                         'Incorrect chain source')
        self.assertEqual(self.chain[0].destination, self.chain[1],
                         'Incorrect chain link')
        self.assertEqual(self.chain[1].source, self.chain[0],
                         'Incorrect chain link')
        self.assertEqual(self.chain[1].destination, self.chain[2],
                         'Incorrect chain link')
        self.assertEqual(self.chain[2].source, self.chain[1],
                         'Incorrect chain link')
        self.assertEqual(self.chain[2].destination, None,
                         'Incorrect chain destination')

    def test_initial_update_state(self):
        for parameter in self.chain:
            self.assertFalse(parameter.needs_update(),
                             'Incorrect initial chain update state')

    def test_update_tail(self):
        self.chain[2].update()
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertEqual(self.chain[1].get(), 2,
                         'Incorrect side-effect')
        self.assertEqual(self.chain[2].get(), 2,
                         'Incorrect update')

    def test_update_head(self):
        self.chain[0].update()
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertEqual(self.chain[1].get(), 1,
                         'Incorrect update')
        self.assertEqual(self.chain[2].get(), 1,
                         'Incorrect update')

class TestParameterPreprocessorChaining(unittest.TestCase):
    def setUp(self):
        self.chain = [
            Parameter(1),
            ParameterDoubler(),
            Parameter(3)
        ]
        computation_chains.chain(*self.chain)

    def test_update_tail(self):
        self.chain[2].update()
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertEqual(self.chain[1].get(), 2,
                         'Incorrect calculation')
        self.assertEqual(self.chain[2].get(), 2,
                         'Incorrect update')

    def test_update_middle(self):
        self.chain[1].update()
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertEqual(self.chain[1].get(), 2,
                         'Incorrect calculation')
        self.assertEqual(self.chain[2].get(), 2,
                         'Incorrect update')

    def test_update_head(self):
        self.chain[0].update()
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertEqual(self.chain[1].get(), 2,
                         'Incorrect update')
        self.assertEqual(self.chain[2].get(), 2,
                         'Incorrect update')

class TestParameterOffsetChaining(unittest.TestCase):
    def setUp(self):
        self.chain = [
            Parameter(1),
            computation_chains.ParameterOffset(1),
            computation_chains.ParameterOffset(1),
            Parameter(0)
        ]
        computation_chains.chain(*self.chain)

    def test_update_middle_lower(self):
        self.chain[2].update()
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertEqual(self.chain[1].get(), 2,
                         'Incorrect calculation')
        self.assertEqual(self.chain[2].get(), 3,
                         'Incorrect calculation')
        self.assertEqual(self.chain[3].get(), self.chain[2].get(),
                         'Incorrect update')

    def test_update_middle_upper(self):
        self.chain[1].update()
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertEqual(self.chain[1].get(), 2,
                         'Incorrect calculation')
        self.assertEqual(self.chain[2].get(), 3,
                         'Incorrect update')
        self.assertEqual(self.chain[3].get(), self.chain[2].get(),
                         'Incorrect update')

    def test_update_head(self):
        self.chain[0].update()
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertEqual(self.chain[1].get(), 2,
                         'Incorrect update')
        self.assertEqual(self.chain[2].get(), 3,
                         'Incorrect update')
        self.assertEqual(self.chain[3].get(), self.chain[2].get(),
                         'Incorrect update')

    def test_change_middle_offset(self):
        self.chain[1].offset = 0
        self.assertFalse(self.chain[0].needs_update(),
                         'Incorrect side-effect')
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertTrue(self.chain[1].needs_update(),
                        'Incorrect update state')
        self.assertEqual(self.chain[1].get(), 1,
                         'Incorrect update')
        self.assertTrue(self.chain[2].needs_update(),
                        'Incorrect update state')
        self.assertEqual(self.chain[2].get(), 2,
                         'Incorrect update')

    def test_change_head(self):
        self.chain[0].set(0)
        self.assertFalse(self.chain[1].needs_update(),
                         'Incorrect update state')
        self.assertEqual(self.chain[1].get(), 1,
                         'Incorrect update')
        self.assertFalse(self.chain[2].needs_update(),
                         'Incorrect update state')
        self.assertEqual(self.chain[2].get(), 2,
                         'Incorrect update')
        self.assertEqual(self.chain[3].get(), 0,
                         'Incorrect side-effect')
        self.chain[3].update()
        self.assertEqual(self.chain[3].get(), self.chain[2].get(),
                         'Incorrect update')

    def test_change_offset_trivial(self):
        self.chain[1].offset = 1
        self.assertFalse(self.chain[0].needs_update(),
                         'Incorrect side-effect')
        self.assertEqual(self.chain[0].get(), 1,
                         'Incorrect side-effect')
        self.assertFalse(self.chain[1].needs_update(),
                         'Incorrect update state')
        self.assertEqual(self.chain[1].get(), 2,
                         'Incorrect update')
        self.assertFalse(self.chain[2].needs_update(),
                         'Incorrect update state')
        self.assertEqual(self.chain[2].get(), 3,
                         'Incorrect update')

