#!/usr/bin/env python2
import unittest
import time
import ctypes

import numpy as np

from utilities import parallelism
from data import data, arrays

def make_small_array(i):
    return np.array([[i, i + 1], [i + 2, i + 3]]).astype(int)

class ArrayDoubleBufferClient(parallelism.DoubleBufferedProcess):
    def __init__(self, *args, **kwargs):
        super(ArrayDoubleBufferClient, self).__init__(
            arrays.DoubleBuffer, 1, 1)
        self.double_buffer.initialize(ctypes.c_int, (2, 2))

    # From Process

    def on_run_start(self):
        self.send_output('started')

    def execute(self, next_input):
        if next_input[0] == 'write':
            time.sleep(0.05)
            self.write_to_buffer(make_small_array(next_input[1]))
        elif next_input[0] == 'read':
            self.send_output(self.unmarshal_output(None, self.double_buffer.read_buffer))
        elif next_input[0] == 'swap':
            self.swap_buffers()
            self.send_output('swap')

    def on_run_parent_start(self):
        parallelism.acquire_lock_poll(self.double_buffer.read_lock, block=True, timeout=1)

    # From DoubleBufferedProcess

    def on_write_to_buffer(self, data, write_buffer):
        np.copyto(write_buffer, data)

    def unmarshal_output(self, marshalled, read_buffer):
        return read_buffer

class TestArrayDoubleBuffer(unittest.TestCase):
    def parallelsafe_setUp(self):
        self.process = ArrayDoubleBufferClient()
        self.process.run_parallel()
        self.assertEqual(self.process.receive_output(), 'started',
                         'Incorrect initialization')

    def assert_read_buffer_consistency(self):
        self.assertEqual(self.process.read_buffer.tolist(),
                         self.round_trip('read').tolist(),
                         'Double buffer inconsistency')

    def round_trip(self, *input_args):
        self.process.send_input(input_args)
        return self.process.receive_output()

    def test_child_writes(self):
        self.parallelsafe_setUp()
        self.process.send_input(('write', 0))
        self.process.swap_buffers()
        self.assertEqual(self.round_trip('read').tolist(), [[0, 1], [2, 3]],
                         'Incorrect synchronization')
        self.assert_read_buffer_consistency()
        for i in range(1, 10):
            self.assertEqual(self.round_trip('read').tolist(), [[i - 1, i], [i + 1, i + 2]],
                             'Incorrect synchronization')
            self.assert_read_buffer_consistency()
            self.process.send_input(('write', i))
            self.process.swap_buffers()

    def test_parent_writes(self):
        self.parallelsafe_setUp()
        self.process.write_to_buffer(make_small_array(0))
        self.round_trip('swap')
        self.assertEqual(self.round_trip('read').tolist(), [[0, 1], [2, 3]],
                         'Incorrect synchronization')
        self.assert_read_buffer_consistency()
        for i in range(1, 10):
            self.assertEqual(self.round_trip('read').tolist(), [[i - 1, i], [i + 1, i + 2]],
                             'Incorrect synchronization')
            self.assert_read_buffer_consistency()
            self.process.write_to_buffer(make_small_array(i))
            self.process.swap_buffers()

    def tearDown(self):
        if self.process.process_running:
            self.process.terminate()

class ArrayLoader(data.DataLoader, data.DataGenerator, arrays.ArraySource):
    def __init__(self):
        self.i = 0

    # From DataGenerator

    def next(self):
        result = make_small_array(self.i)
        self.i += 1
        return result

    def reset(self):
        self.i = 0

    # From ArraySource

    @property
    def array_ctype(self):
        return ctypes.c_int

    @property
    def array_shapes(self):
        return (2, 2)
