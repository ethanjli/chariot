#!/usr/bin/env python2
import unittest
import time
import random
import sys
import ctypes
from multiprocessing import Value
try:
    from Queue import Empty, Full
except ImportError:
    from queue import Empty, Full

from data import data
from utilities import parallelism

class Process(parallelism.Process):
    def __init__(self, queue_size):
        super(Process, self).__init__(queue_size, queue_size)

    def execute(self, next_input):
        if next_input[0] == 'double':
            output = 2 * next_input[1]
            time.sleep(0.05)
            self.send_output(output)

class HangingProcess(parallelism.Process):
    def __init__(self, test_case):
        super(HangingProcess, self).__init__(1, 1)
        self.test_case = test_case

    def on_run_start(self):
        self.send_output('started')

    def execute(self, next_input):
        if next_input == 'spin':
            try:
                for counter in range(100):
                    time.sleep(0.05)
                    if counter == 0:
                        self.send_output('starting to spin')
                    counter += 1
                self.send_output((True, 'Hanging process should have caught SIGINT'))
            except KeyboardInterrupt:
                self.send_output((False, 'Hanging process caught SIGINT'))
        elif next_input == 'hang_send_output':
            self.send_output('ready to hang')
            try:
                self.send_output('hanging')
                self.send_output((True, 'Hanging process should have caught SIGINT'))
            except KeyboardInterrupt:
                self.send_output((False, 'Hanging process caught SIGINT'))

class TestProcess(unittest.TestCase):
    def setUp(self):
        self.tight_process = Process(1)
        self.loose_process = Process(11)
        self.hanging_process = HangingProcess(self)

    def assert_full(self, queue):
        try:
            queue.put(None, False)
            self.assertFalse(True, 'Queue should have been full')
        except Full:
            pass

    def assert_empty(self, queue):
        try:
            queue.get(False)
            self.assertFalse(True, 'Queue should have been empty')
        except Empty:
            pass

    def test_interrupt_waiting_for_input(self):
        self.hanging_process.run_parallel()
        self.hanging_process.receive_output()
        self.hanging_process.kill()
        self.hanging_process.terminate()

    def test_interrupt_hanging_send_output(self):
        self.hanging_process.run_parallel()
        self.hanging_process.receive_output()
        self.hanging_process.send_input('hang_send_output')
        self.hanging_process.receive_output()
        self.hanging_process.kill()
        self.hanging_process.receive_output()
        assert_result = self.hanging_process.receive_output()
        self.assertFalse(assert_result[0], assert_result[1])
        self.hanging_process.terminate()

    def test_interrupt_spinning(self):
        self.hanging_process.run_parallel()
        self.hanging_process.receive_output()
        self.hanging_process.send_input('spin')
        self.hanging_process.receive_output()
        self.hanging_process.kill()
        assert_result = self.hanging_process.receive_output()
        self.assertFalse(assert_result[0], assert_result[1])
        self.hanging_process.terminate()

    def test_terminate(self):
        self.tight_process.run_parallel()
        self.assertTrue(self.tight_process.process_running, 'Incorrect process state')
        self.tight_process.terminate()
        self.assertFalse(self.tight_process.process_running, 'Incorrect process state')
        self.assert_empty(self.tight_process._output_queue)

    def test_tight_execute(self):
        self.tight_process.run_parallel()
        for i in range(10):
            self.tight_process.send_input(('double', i))
            self.assertEqual(self.tight_process.receive_output(), i * 2,
                             'Incorrect process synchronization')
        self.assert_empty(self.tight_process._output_queue)
        self.tight_process.terminate()

    def test_loose_execute(self):
        self.loose_process.run_parallel()
        for i in range(10):
            self.loose_process.send_input(('double', i))
        self.loose_process.terminate()
        for i in range(10):
            self.assertEqual(self.loose_process.receive_output(), i * 2,
                             'Incorrect process synchronization')
        self.assert_empty(self.loose_process._output_queue)

    def test_loose_fill(self):
        self.loose_process.run_parallel()
        for i in range(22):
            self.loose_process.send_input(('double', i))
        self.assert_full(self.loose_process._input_queue)
        for i in range(22):
            self.assertEqual(self.loose_process.receive_output(), i * 2,
                             'Incorrect process synchronization')
        self.assert_empty(self.loose_process._output_queue)
        self.loose_process.terminate()

    def tearDown(self):
        if self.tight_process.process_running:
            self.tight_process.terminate()
        if self.loose_process.process_running:
            self.loose_process.terminate()
        if self.hanging_process.process_running:
            self.hanging_process.terminate(force_terminate=True)

class ValueDoubleBuffer(parallelism.DoubleBuffer):
    def __init__(self):
        super(ValueDoubleBuffer, self).__init__()
        self._values = [Value(ctypes.c_int), Value(ctypes.c_int)]
        self._values[0].value = 0
        self._values[1].value = 0

    def get_buffer(self, buffer_id):
        return self._values[buffer_id]

class DoubleBufferedProcess(parallelism.Process):
    def __init__(self):
        super(DoubleBufferedProcess, self).__init__(1, 1)
        self.double_buffer = ValueDoubleBuffer()

    def execute(self, next_input):
        if next_input[0] == 'swap':
            self.double_buffer.swap()
            self.send_output(next_input)
        elif next_input[0] == 'read_value':
            if next_input[1] == 'read':
                buf = self.double_buffer.read_buffer
            elif next_input[1] == 'write':
                buf = self.double_buffer.write_buffer
            self.send_output(('read_value', next_input[1], buf.value))
        elif next_input[0] == 'write_value':
            if next_input[1] == 'read':
                buf = self.double_buffer.read_buffer
            elif next_input[1] == 'write':
                buf = self.double_buffer.write_buffer
            buf.value = next_input[2]
            self.send_output(next_input)
        elif next_input[0] == 'acquire_lock':
            if next_input[1] == 'read':
                lock = self.double_buffer.read_lock
            elif next_input[1] == 'write':
                lock = self.double_buffer.write_lock
            lock.acquire()
            self.send_output(next_input)
        elif next_input[0] == 'release_lock':
            if next_input[1] == 'read':
                lock = self.double_buffer.read_lock
            elif next_input[1] == 'write':
                lock = self.double_buffer.write_lock
            lock.release()
            self.send_output(next_input)
        elif next_input[0] == 'query_lock':
            if next_input[1] == 'read':
                lock = self.double_buffer.read_lock
            elif next_input[1] == 'write':
                lock = self.double_buffer.write_lock
            previously_unlocked = lock.acquire(False)
            if previously_unlocked:
                lock.release()
            self.send_output(('query_lock', next_input[1],
                              'unlocked' if previously_unlocked else 'locked'))

class TestDoubleBuffer(unittest.TestCase):
    def setUp(self):
        self.double_buffer = ValueDoubleBuffer()

    def test_init(self):
        self.assertEqual(self.double_buffer.read_id, 0,
                         'Incorrect initialization')
        self.assertEqual(self.double_buffer.write_id, 1,
                         'Incorrect initialization')

    def test_swap(self):
        self.double_buffer.read_buffer.value = 1
        self.double_buffer.swap()
        self.double_buffer.read_buffer.value = 2
        self.double_buffer.swap()
        self.assertEqual(self.double_buffer.read_buffer.value, 1,
                         'Incorrect double buffer swap')
        self.double_buffer.swap()
        self.assertEqual(self.double_buffer.read_buffer.value, 2,
                         'Incorrect double buffer swap')

class TestDoubleBufferSynchronization(unittest.TestCase):
    def setUp(self):
        self.process = DoubleBufferedProcess()
        self.process.run_parallel()

    def is_unlocked(self, lock):
        previously_unlocked = lock.acquire(False)
        if previously_unlocked:
            lock.release()
        return previously_unlocked

    def round_trip(self, *input_args):
        self.process.send_input(input_args)
        return self.process.receive_output()

    def assert_parent_value(self, read_expected, write_expected, error_message):
        self.assertEqual(self.process.double_buffer.read_buffer.value, read_expected,
                         error_message)
        self.assertEqual(self.process.double_buffer.write_buffer.value, write_expected,
                         error_message)

    def assert_child_value(self, read_expected, write_expected, error_message):
        self.assertEqual(self.round_trip('read_value', 'read'),
                         ('read_value', 'read', read_expected),
                         error_message)
        self.assertEqual(self.round_trip('read_value', 'write'),
                         ('read_value', 'write', write_expected),
                         error_message)

    def test_value_synchronization_to_child(self):
        self.process.double_buffer.read_buffer.value = 1
        self.process.double_buffer.write_buffer.value = 2
        self.assert_child_value(1, 2, 'Incorrect value synchronization from parent to child')

        self.process.double_buffer.read_buffer.value = 3
        self.assert_child_value(3, 2, 'Incorrect value synchronization from parent to child')

        self.process.double_buffer.write_buffer.value = 4
        self.assert_child_value(3, 4, 'Incorrect value synchronization from parent to child')

    def test_value_synchronization_from_child(self):
        self.round_trip('write_value', 'read', 1)
        self.round_trip('write_value', 'write', 2)
        self.assert_parent_value(1, 2, 'Incorrect value synchronization from child to parent')

        self.round_trip('write_value', 'read', 3)
        self.assert_parent_value(3, 2, 'Incorrect value synchronization from child to parent')
        self.round_trip('write_value', 'write', 4)
        self.assert_parent_value(3, 4, 'Incorrect value synchronization from child to parent')

    def test_parent_swap(self):
        self.process.double_buffer.read_buffer.value = 1
        self.process.double_buffer.write_buffer.value = 2
        self.process.double_buffer.swap()
        self.assert_parent_value(2, 1, 'Incorrect swap synchronization')

        self.process.double_buffer.swap()
        self.assert_parent_value(1, 2, 'Incorrect swap synchronization')

    def assert_parent_lock_state(self, read_unlocked, write_unlocked, error_message):
        read_assert = self.assertTrue if read_unlocked else self.assertFalse
        write_assert = self.assertTrue if write_unlocked else self.assertFalse
        read_assert(self.is_unlocked(self.process.double_buffer.read_lock),
                    error_message)
        write_assert(self.is_unlocked(self.process.double_buffer.write_lock),
                     error_message)

    def assert_child_lock_state(self, read_unlocked, write_unlocked, error_message):
        read_expected = 'unlocked' if read_unlocked else 'locked'
        write_expected = 'unlocked' if write_unlocked else 'locked'
        self.assertEqual(self.round_trip('query_lock', 'read'),
                         ('query_lock', 'read', read_expected),
                         error_message)
        self.assertEqual(self.round_trip('query_lock', 'write'),
                         ('query_lock', 'write', write_expected),
                         error_message)

    def test_locking_initialization(self):
        self.assert_parent_lock_state(True, True, 'Incorrect lock initialization in parent')
        self.assert_child_lock_state(True, True, 'Incorrect lock initialization in child')

    def test_locking_parent(self):
        self.process.double_buffer.read_lock.acquire()
        self.assert_child_lock_state(False, True,
                                     'Incorrect lock synchronization from parent to child')
        self.process.double_buffer.write_lock.acquire()
        self.assert_child_lock_state(False, False,
                                     'Incorrect lock synchronization from parent to child')
        self.process.double_buffer.read_lock.release()
        self.assert_child_lock_state(True, False,
                                     'Incorrect lock synchronization from parent to child')
        self.process.double_buffer.write_lock.release()
        self.assert_child_lock_state(True, True,
                                     'Incorrect lock synchronization from parent to child')

    def test_locking_child(self):
        self.round_trip('acquire_lock', 'read')
        self.assert_parent_lock_state(False, True,
                                      'Incorrect lock synchronization from child to parent')
        self.round_trip('acquire_lock', 'write')
        self.assert_parent_lock_state(False, False,
                                      'Incorrect lock synchronization from child to parent')
        self.round_trip('release_lock', 'read')
        self.assert_parent_lock_state(True, False,
                                      'Incorrect lock synchronization from child to parent')
        self.round_trip('release_lock', 'write')
        self.assert_parent_lock_state(True, True,
                                      'Incorrect lock synchronization from child to parent')

    def tearDown(self):
        if self.process.process_running:
            self.process.terminate()

class ValueLoader(data.DataLoader, data.DataGenerator):
    def __init__(self, length, random_floor=0,
                 loader_initialization_delay=0, generation_delay=0):
        self.i = 0
        self.length = length
        self.random_floor = random_floor
        self.loader_initialization_delay = loader_initialization_delay
        self.generation_delay = generation_delay

    # From DataGenerator

    def next(self):
        if self.i >= self.length:
            raise StopIteration
        result = self.i * 2
        self.i += 1
        time.sleep(random.uniform(self.generation_delay * self.random_floor,
                                  self.generation_delay))
        return result

    def reset(self):
        self.i = 0

    # From DataLoader

    def load(self):
        time.sleep(random.uniform(self.loader_initialization_delay * self.random_floor,
                                  self.loader_initialization_delay))

class ValueLoaderGeneratorProcess(parallelism.LoaderGeneratorProcess):
    def __init__(self, *args, **kwargs):
        super(ValueLoaderGeneratorProcess, self).__init__(
            ValueDoubleBuffer(), lambda: ValueLoader(*args, **kwargs))

    # From LoaderGeneratorProcess

    def _on_load(self, loaded_next):
        self.double_buffer.write_buffer.value = loaded_next
        return loaded_next

    def _process_result(self, result):
        return self.double_buffer.read_buffer.value

class TestLoaderGeneratorProcess(unittest.TestCase):
    def setUp(self):
        self.random_floors = [1, 0.5]
        self.initialization_delays = [0, 0.01]
        self.first_next_delays = [0, 0.01]
        self.generation_delays = [0, 0.01]
        self.consecutive_next_delays = [0, 0.01]
        self.repetitions = 10

    def assert_even_generation(self, length, random_floor,
                               first_next_delay=0, consecutive_next_delay=0):
        time.sleep(random.uniform(first_next_delay * random_floor, first_next_delay))
        for i in range(length):
            try:
                result = next(self.loader)
                self.assertEqual(result, 2 * i, 'Incorrect generation')
                time.sleep(random.uniform(consecutive_next_delay * random_floor,
                                          consecutive_next_delay))
            except StopIteration:
                self.assertFalse(True, 'Extraneous StopIteration')

    def assert_stopiteration(self, message):
        try:
            next(self.loader)
            self.assertFalse(True, message)
        except StopIteration:
            pass

    def assert_short_generation(self, length, random_floor,
                                first_next_delay=0, consecutive_next_delay=0):
        time.sleep(random.uniform(first_next_delay * random_floor, first_next_delay))
        for i in range(2 * length):
            try:
                result = next(self.loader)
                self.assertEqual(result, 2 * i, 'Incorrect generation')
                time.sleep(random.uniform(consecutive_next_delay * random_floor,
                                          consecutive_next_delay))
            except StopIteration:
                self.assertEqual(i, length, 'Incorrect StopIteration')
                break
        for i in range(length):
            self.assert_stopiteration('Missing StopIteration')

    def test_null_generation(self):
        sys.stdout.write('null[')
        for random_floor in self.random_floors:
            for initialization_delay in self.initialization_delays:
                for first_next_delay in self.first_next_delays:
                    sys.stdout.write('[')
                    for _ in range(self.repetitions):
                        self.loader = ValueLoaderGeneratorProcess(
                            0, random_floor, initialization_delay)
                        self.loader.load()
                        time.sleep(random.uniform(first_next_delay * random_floor,
                                                  first_next_delay))
                        self.assert_short_generation(0, random_floor, first_next_delay)
                        self.loader.stop_loading()
                        sys.stdout.write('.')
                    sys.stdout.write(']')
        print(']')

    def test_single_generation(self):
        sys.stdout.write('single[')
        for random_floor in self.random_floors:
            for initialization_delay in self.initialization_delays:
                for first_next_delay in self.first_next_delays:
                    sys.stdout.write('[')
                    for _ in range(self.repetitions):
                        self.loader = ValueLoaderGeneratorProcess(
                            1, random_floor, initialization_delay)
                        self.loader.load()
                        time.sleep(random.uniform(first_next_delay * random_floor,
                                                  first_next_delay))
                        self.assert_short_generation(1, random_floor, first_next_delay)
                        self.loader.stop_loading()
                        sys.stdout.write('.')
                    sys.stdout.write(']')
        print(']')

    def test_even_generation(self):
        sys.stdout.write('even[')
        for random_floor in self.random_floors:
            for generation_delay in self.generation_delays:
                for consecutive_next_delay in self.consecutive_next_delays:
                    sys.stdout.write('[')
                    for _ in range(self.repetitions):
                        self.loader = ValueLoaderGeneratorProcess(
                            10, generation_delay=generation_delay)
                        self.loader.load()
                        self.assert_even_generation(
                            10, random_floor, consecutive_next_delay=consecutive_next_delay)
                        self.loader.stop_loading()
                        sys.stdout.write('.')
                    sys.stdout.write(']')
        print(']')

    def test_generation(self):
        sys.stdout.write('gen[')
        for random_floor in self.random_floors:
            for generation_delay in self.generation_delays:
                for consecutive_next_delay in self.consecutive_next_delays:
                    sys.stdout.write('[')
                    for _ in range(self.repetitions):
                        self.loader = ValueLoaderGeneratorProcess(
                            10, generation_delay=generation_delay)
                        self.loader.load()
                        self.assert_short_generation(
                            10, random_floor, consecutive_next_delay=consecutive_next_delay)
                        self.loader.stop_loading()
                        sys.stdout.write('.')
                    sys.stdout.write(']')
        print(']')

    def tearDown(self):
        if self.loader.process_running:
            self.loader.stop_loading()

