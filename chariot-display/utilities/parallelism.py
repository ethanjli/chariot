#!/usr/bin/env python2
"""Classes to enable painless process-level parallelism."""
import traceback
import os
import signal
import operator
import multiprocessing
from multiprocessing import Array, Value
import ctypes
try:
    from Queue import Empty
except ImportError:
    from queue import Empty
try:
    from _thread import interrupt_main
except ImportError:
    from thread import interrupt_main

import numpy as np
from numpy.ctypeslib import as_array

from data import data
import concurrency

# WORKER POOLS

class EarlyTermination(Exception):
    """A custom exception used when multiprocessing workers are terminated early.
    Raise this when the worker in a pool needs to terminate early.
    """
    pass

class Workset():
    """An interface for embarrassingly parallelizable work.
    Extend this to implement a set of work units for a worker pool to handle.
    """

    def work(self, work_id):
        """The method which gets executed on each worker, with a unique work_id."""
        pass

    def work_ids(self):
        """The method which defines the immutable work_ids for the work units."""

    def handle_early_termination(self, work_id):
        """The method called when a worker is terminated early by Ctrl+C."""
        pass

    def handle_exception(self, work_id, e):
        """The method called when a worker is terminated early by an exception."""
        pass

    def __call__(self, work_id):
        try:
            self.work(work_id)
        except EarlyTermination:
            self.handle_early_termination(work_id)
        except Exception as e:
            self.handle_exception(work_id, e)

    def execute_sequential(self):
        """Executes work sequentially in the current process."""
        for work_id in self.work_ids():
            self(work_id)

    def execute_parallel(self, num_processes=(multiprocessing.cpu_count() - 1)):
        print('Initializing pool of ' + str(num_processes) + ' worker processes...')
        pool = multiprocessing.Pool(processes=num_processes)
        try:
            print('Distributing work across workers...')
            pool.map(self, self.work_ids())
            pool.close()
            print('Finished work.')
        except (KeyboardInterrupt, EarlyTermination):
            print('Terminating work pool...')
            pool.terminate()
            print('Terminated work pool.')
        except Exception as e:
            print(e)
            print('Terminating pool...')
            pool.terminate()
            print('Terminated pool.')
        finally:
            print('Joining workers.')
            pool.join()
            print('Finished.')

# SYNCHRONIZED PARALLELISM

def flush_queue(queue):
    try:
        for item in iter(queue.get_nowait, None):
            pass
    except Empty:
        pass

class DoubleBuffer(object):
    """Abstract base class for double buffering.
    The read buffer is used for reading, while the write buffer is used for writing
    the next read buffer.
    Note that only the locks and event are synchronized across processes.
    """
    def __init__(self):
        self._buffer_id = Value(ctypes.c_int)
        self._buffer_id.value = 0
        self._buffer_locks = [multiprocessing.Lock(), multiprocessing.Lock()]
        self._buffer_readable_events = [multiprocessing.Event(), multiprocessing.Event()]

    def get_buffer(self, buffer_id):
        """Gets the buffer at the specified id.
        Implement this. Only Value and Array-backed references in the buffer will be synchronized.
        """
        pass

    def swap(self):
        self._buffer_id.value = 1 - self._buffer_id.value

    @property
    def read_id(self):
        return self._buffer_id.value

    @property
    def write_id(self):
        return 1 - self._buffer_id.value

    @property
    def read_buffer(self):
        return self.get_buffer(self.read_id)

    @property
    def write_buffer(self):
        return self.get_buffer(self.write_id)

    @property
    def read_lock(self):
        return self._buffer_locks[self.read_id]

    @property
    def write_lock(self):
        return self._buffer_locks[self.write_id]

    @property
    def read_readable(self):
        return self._buffer_readable_events[self.read_id]

    @property
    def write_readable(self):
        return self._buffer_readable_events[self.write_id]

    def release_locks(self):
        for lock in self._buffer_locks:
            try:
                lock.release()
            except ValueError:
                pass

    def reset(self):
        self.read_readable.clear()
        self.write_readable.clear()

class ExceptionListener(concurrency.Thread):
    """A thread which passes exceptions from an associated child process.
    Listens for exceptions received by the send method from any process.
    Upon receipt of an exception, saves exception information to the exception
    attribute, and interrupts the main thread with a KeyboardInterrupt.
    """
    def __init__(self, process_name):
        super(ExceptionListener, self).__init__()
        self.process_name = process_name
        self.queue = multiprocessing.Queue(1)
        self.exception = None

    def send(self, child_name, child_pid, e, traceback):
        self.queue.put({
            'child_name': child_name,
            'child_pid': child_pid,
            'exception': e,
            'traceback': traceback
        })

    def receive_exception(self, block=True, timeout=0.1):
        exception_received = False
        try:
            self.exception = self.queue.get(block, timeout)
            exception_received = True
        except Empty:
            pass
        if exception_received:
            print('Interrupting main thread from ' +
                  repr(self.exception['exception']) +
                  ' raised in child ' + self.exception['child_name'] +
                  ' (pid ' + str(self.exception['child_pid']) + '):\n' +
                  self.exception['traceback'])
            interrupt_main()

    # From Thread

    @property
    def name(self):
        return self.process_name + ' ' + self.__class__.__name__

    def execute(self):
        self.receive_exception()


class Process(object):
    """Abstract base class for child processes synchronized over input and output queues.
    Data in the input queue is processed in FIFO order.
    None in the input queue is a sentinel for the child process to exit.
    Exceptions in the child process are saved in the exception property; uncaught
    exceptions raised from the child process will interrupt the main thread with a
    KeyboardInterrupt.
    """
    def __init__(self, max_input_queue_size, max_output_queue_size, *args, **kwargs):
        super(Process, self).__init__(*args, **kwargs)
        self.__process = None
        self._input_queue = multiprocessing.Queue(max_input_queue_size)
        self._output_queue = multiprocessing.Queue(max_output_queue_size)
        self.__exception_listener = ExceptionListener(self.name)

    @property
    def name(self):
        """The name of the process.
        Override this to use something other than the name of the derived class."""
        return self.__class__.__name__

    @property
    def process_running(self):
        return self.__process is not None

    @property
    def pid(self):
        return self.__process.pid

    # Child methods

    def on_run_start(self):
        """Do any work in the child before execute starts being called.
        Implement this."""
        pass

    def execute(self, next_input):
        """Do work on the input
        Implement this with an input handler."""
        pass

    def on_run_finish(self):
        """Do any work in the child after execute stops being called.
        Implement this."""
        pass

    def receive_input(self, block=True, timeout=1):
        """Retrieve the next input from the input queue.
        By default, this blocks with a timeout of 1 to allow preemptive child
        termination with a max delay of 1 second if the child is already active and
        waiting for input when it receives an interrupt.
        """
        while True:
            try:
                next_input = self._input_queue.get(block, timeout)
                return next_input
            except Empty:
                pass

    def send_output(self, next_output, block=True, timeout=None):
        self._output_queue.put(next_output, block, timeout)

    def send_exception(self, child_name, child_pid, e, traceback):
        self.__exception_listener.send(child_name, child_pid, e, traceback)

    def run_serial(self, block=True, timeout=1):
        """Perform the work in the current execution thread.
        Only usable if inputs and outputs are being exchanged with another thread."""
        try:
            self.on_run_start()
            while True:
                    next_input = self.receive_input(block, timeout)
                    if next_input is None:
                        break
                    else:
                        self.execute(next_input)
            self.on_run_finish()
        except BaseException as e:
            print('Raising exception from child ' + self.name +
                  ' (pid ' + str(self.pid) + ') to parent:')
            print(repr(e))
            traceback.print_exc()
            self.send_exception(self.name, self.pid, e, traceback.format_exc())

    # Parent methods

    @property
    def exception(self):
        """The last-raised exception.
        If no exception has been raised, returns None."""
        return self.__exception_listener.exception

    def on_run_parent_start(self):
        """Do any work in the parent when run_parallel is called.
        Implement this."""
        pass

    def run_parallel(self):
        """Perform the work in a new parallel process.
        Catch KeyboardInterrupts and check the exception property to catch exceptions
        from the child."""
        if self.process_running:
            return
        self.__process = multiprocessing.Process(
            target=self.run_serial, name=self.name
        )
        self.__exception_listener.run_concurrent()
        self.__process.start()
        self.on_run_parent_start()

    def send_input(self, next_input, block=True, timeout=None):
        self._input_queue.put(next_input, block, timeout)

    def receive_output(self, block=True, timeout=1):
        while True:
            try:
                next_output = self._output_queue.get(block, timeout)
                return next_output
            except Empty:
                pass

    def on_terminate(self):
        """Do any work in the parent right before termination.
        Implement this."""
        pass

    def on_terminate_finish(self):
        """Do any work in the parent right after termination.
        Implement this."""
        pass

    def terminate(self, force_terminate=False):
        self.on_terminate()
        if not self.process_running:
            return
        self.__exception_listener.terminate()
        if force_terminate:
            self.__process.terminate()
        else:
            self.send_input(None)
            self.__process.join()
        self.__process = None
        self.on_terminate_finish()

    def kill(self, sig=signal.SIGINT):
        os.kill(self.pid, sig)

class LoaderGeneratorProcess(Process, data.DataLoader, data.DataGenerator):
    """A Loader/Generator which runs in a separate process."""
    def __init__(self, DoubleBufferFactory, LoaderGeneratorFactory, *args, **kwargs):
        super(LoaderGeneratorProcess, self).__init__(1, 1, *args, **kwargs)
        self.double_buffer = DoubleBufferFactory()
        self.loader = LoaderGeneratorFactory()
        self.buffer_ready = multiprocessing.Event()

    # Child methods

    def _load_next(self):
        try:
            loaded_next = next(self.loader)
            # Lock the write buffer to write to it
            with self.double_buffer.write_lock:
                output = {
                    'next': self._on_load(loaded_next)
                }
                self.double_buffer.write_readable.set()
                self.send_output(output)
        except StopIteration:
            self.double_buffer.write_readable.set()
            self.send_output(None)

    # From Process

    def on_run_parent_start(self):
        self.double_buffer.read_lock.acquire()  # prepare for the assumptions of the next() call
        self.send_input('next')  # let child load the first value into the write buffer

    def on_terminate_finish(self):
        super(LoaderGeneratorProcess, self).stop_loading()

    def on_run_start(self):
        self.loader.load()

    def execute(self, next_input):
        if next_input == 'next':
            self._load_next()

    def on_run_finish(self):
        self.loader.stop_loading()

    # From DataGenerator

    def next(self, block=True, timeout=1):
        # Assumes the parent has the read lock and no longer needs the read buffer's data
        self.double_buffer.write_readable.wait()
        # Lock the write buffer so we can read from it when it becomes a read buffer
        while not self.double_buffer.write_lock.acquire(block, timeout):
            pass
        # Swap buffers, so that our locked buffer becomes the new read buffer
        self.double_buffer.swap()
        # Reset and release our unneeded buffer as the new write buffer
        self.double_buffer.write_readable.clear()
        self.double_buffer.write_lock.release()
        # Let the child start writing to the new write buffer
        self.send_input('next')

        # Receive the output associated with the new read buffer
        output = self.receive_output()
        if output is not None:
            processed_result = self._process_result(output['next'])
            return processed_result
        else:
            raise StopIteration

    def reset(self):
        self.stop_loading()
        self.double_buffer.reset()
        self.double_buffer.release_locks()
        flush_queue(self._input_queue)
        flush_queue(self._output_queue)
        flush_queue(self.__exception_queue)

    # From DataLoader

    def load(self):
        self.run_parallel()

    def stop_loading(self):
        self.terminate()

# ARRAY LOADING

class ArrayDoubleBuffer(DoubleBuffer):
    def __init__(self):
        super(ArrayDoubleBuffer, self).__init__()
        self._array_bases = [None, None]
        self._arrays = [None, None]

    def initialize(self, ctype, shape):
        num_elements = reduce(operator.mul, shape, 1)

        self._array_bases[0] = Array(ctype, num_elements)
        self._array_bases[1] = Array(ctype, num_elements)

        self._arrays[0] = np.ctypeslib.as_array(
            self._array_bases[0].get_obj()).reshape(*shape)
        self._arrays[1] = as_array(
            self._array_bases[1].get_obj()).reshape(*shape)

    @property
    def current_array(self):
        return self._arrays[self.current_id]

    @property
    def shadow_array(self):
        return self._arrays[self.shadow_id]

    def get_array(self, buffer_id):
        return self._arrays[buffer_id]

class ArrayLoader(LoaderGeneratorProcess, data.ArraySource):
    """Loads numpy arrays sequentially in a separate process into shared memory.
    PreloadingConcurrentDataLoader should also implement the ArraySource interface."""
    def __init__(self, *args, **kwargs):
        super(ArrayLoader, self).__init__(ArrayDoubleBuffer(), *args, **kwargs)

        self._buffer.initialize(self._loader.get_array_ctype(),
                                self._loader.get_array_shape())

    # From LoaderGenerator

    def _on_load(self, loaded_next, target_buffer):
        np.copyto(self._buffer.get_array(target_buffer), loaded_next)
        return None

    def _process_result(self, result):
        return self._buffer.current_array

    # From ArraySource

    @property
    def array_ctype(self):
        return self._loader.get_array_ctype()

    @property
    def array_shape(self):
        return self._loader.get_array_shape()

# CHUNK LOADING

class FakeChunk():
    def __init__(self, array, attrs):
        self._array = array
        self.attrs = attrs

    def __getitem__(self, key):
        return self._array.__getitem__(key)

class ChunkLoader(ArrayLoader):
    def __init__(self, *args, **kwargs):
        super(ChunkLoader, self).__init__(data.ConcurrentDataChunkLoader, *args, **kwargs)
        self.lazy = False

    def _on_load(self, loaded_next, target_buffer):
        super(ChunkLoader, self)._on_load(loaded_next[1], target_buffer)
        attrs = loaded_next[0].attrs
        return dict(attrs)

    def _process_result(self, result):
        array = self._buffer.current_array
        return (FakeChunk(array, result), array)

# POINT CLOUD GENERATION

class PointCloudDoubleBuffer(DoubleBuffer):
    def __init__(self, num_components=2):
        super(PointCloudDoubleBuffer, self).__init__()
        self._point_cloud_bases = [[None for _ in range(num_components)],
                                   [None for _ in range(num_components)]]
        self._point_clouds = [[None for _ in range(num_components)],
                              [None for _ in range(num_components)]]
        self._num_points = [None, None]

    def initialize(self, ctype, shape):
        num_elements = reduce(operator.mul, shape, 1)

        self._locks = [multiprocessing.RLock(), multiprocessing.RLock()]

        self._point_cloud_bases[0] = [Array(ctype, num_elements, lock=self._locks[0])
                                      for _ in range(len(self._point_cloud_bases[0]))]
        self._point_cloud_bases[1] = [Array(ctype, num_elements, lock=self._locks[1])
                                      for _ in range(len(self._point_cloud_bases[1]))]

        self._point_clouds[0] = [as_array(base.get_obj()).reshape(*shape)
                                 for base in self._point_cloud_bases[0]]
        self._point_clouds[1] = [as_array(base.get_obj()).reshape(*shape)
                                 for base in self._point_cloud_bases[1]]

        self._num_points[0] = Value(ctypes.c_int, 0, lock=self._locks[0])
        self._num_points[1] = Value(ctypes.c_int, 0, lock=self._locks[1])

    @property
    def current_point_cloud(self):
        return self._point_clouds[self.current_id]

    @property
    def shadow_point_cloud(self):
        return self._point_clouds[self.shadow_id]

    @property
    def num_current_points(self):
        return self._num_points[self.current_id]

    @property
    def num_shadow_points(self):
        return self._num_points[self.shadow_id]

    def get_point_cloud(self, buffer_id):
        return self._point_clouds[buffer_id]

    def get_num_points(self, buffer_id):
        return self._num_points[buffer_id]

class PointCloudGenerator(LoaderGeneratorProcess):
    """Generates point clouds sequentially in a separate process into shared memory."""
    def __init__(self, *args, **kwargs):
        super(PointCloudGenerator, self).__init__(PointCloudDoubleBuffer(), *args, **kwargs)

        self._loader.load()  # Sometimes needed to calculate the array shape
        self._loader.stop_loading()  # We want to start the loader from our child process so we can join it
        self._loader.reset()
        self._buffer.initialize(self._loader.get_array_ctype(),
                                self._loader.get_array_shape())

    @property
    def time_range(self):
        return self._loader.time_range

    def get_times(self):
        return self._loader.get_times()

    # From LoaderGenerator

    def _on_load(self, loaded_next, target_buffer):
        num_points = loaded_next[0].shape[0]
        num_allowed_points = self.get_array_shape()[0]
        if num_points > num_allowed_points:
            print(self.__class__.__name__ + ' Warning: buffer can only hold ' +
                  str(num_allowed_points) + ' of the ' + str(num_points) +
                  ' points in the cloud!')
        num_points = min(num_points, num_allowed_points)
        self._buffer.get_num_points(target_buffer).value = num_points
        for (index, array) in enumerate(loaded_next):
            np.copyto(self._buffer.get_point_cloud(target_buffer)[index][:num_points],
                      array[:num_points])
        return None

    def _process_result(self, result):
        num_points = self._buffer.num_current_points.value
        return [array[:num_points] for array in self._buffer.current_point_cloud]

    def reset(self):
        super(PointCloudGenerator, self).reset()
        self._loader.reset()

    # From ArraySource

    def get_array_ctype(self):
        return self._loader.get_array_ctype()

    def get_array_shape(self):
        return self._loader.get_array_shape()

# POINT CLOUD AND MESH GENERATION

class MeshDoubleBuffer(PointCloudDoubleBuffer):
    def __init__(self, *args, **kwargs):
        super(MeshDoubleBuffer, self).__init__(*args, **kwargs)
        self._mesh_bases = [[None, None, None],
                            [None, None, None]]
        self._meshes = [[None, None, None],
                        [None, None, None]]
        self._num_vertices = [None, None]
        self._num_faces = [None, None]

    def initialize(self, array_ctypes, array_shapes):
        super(MeshDoubleBuffer, self).initialize(array_ctypes[0], array_shapes[0])

        num_vertices = reduce(operator.mul, array_shapes[1], 1)
        num_faces = reduce(operator.mul, array_shapes[2], 1)
        self._mesh_bases[0] = [Array(array_ctypes[1], num_vertices, lock=self._locks[0]),
                               Array(array_ctypes[1], num_vertices, lock=self._locks[0]),
                               Array(array_ctypes[2], num_faces, lock=self._locks[0])]
        self._mesh_bases[1] = [Array(array_ctypes[1], num_vertices, lock=self._locks[1]),
                               Array(array_ctypes[1], num_vertices, lock=self._locks[1]),
                               Array(array_ctypes[2], num_faces, lock=self._locks[1])]

        self._meshes[0] = [as_array(self._mesh_bases[0][0].get_obj()).reshape(*array_shapes[1]),
                           as_array(self._mesh_bases[0][1].get_obj()).reshape(*array_shapes[1]),
                           as_array(self._mesh_bases[0][2].get_obj()).reshape(*array_shapes[2])]
        self._meshes[1] = [as_array(self._mesh_bases[1][0].get_obj()).reshape(*array_shapes[1]),
                           as_array(self._mesh_bases[1][1].get_obj()).reshape(*array_shapes[1]),
                           as_array(self._mesh_bases[1][2].get_obj()).reshape(*array_shapes[2])]

        self._num_vertices[0] = Value(ctypes.c_int, 0, lock=self._locks[0])
        self._num_vertices[1] = Value(ctypes.c_int, 0, lock=self._locks[1])
        self._num_faces[0] = Value(ctypes.c_int, 0, lock=self._locks[0])
        self._num_faces[1] = Value(ctypes.c_int, 0, lock=self._locks[1])

    @property
    def current_mesh(self):
        return self._meshes[self.current_id]

    @property
    def shadow_mesh(self):
        return self._meshes[self.shadow_id]

    @property
    def num_current_vertices(self):
        return self._num_vertices[self.current_id]

    @property
    def num_shadow_vertices(self):
        return self._num_vertices[self.shadow_id]

    @property
    def num_current_faces(self):
        return self._num_faces[self.current_id]

    @property
    def num_shadow_faces(self):
        return self._num_faces[self.shadow_id]

    def get_mesh(self, buffer_id):
        return self._meshes[buffer_id]

    def get_num_vertices(self, buffer_id):
        return self._num_vertices[buffer_id]

    def get_num_faces(self, buffer_id):
        return self._num_faces[buffer_id]

class PointCloudMesher(LoaderGeneratorProcess):
    """Generates and meshes point clouds sequentially in a separate process into shared memory.
    Note: _on_load currently assumes that the point cloud consists of exactly two arrays."""
    def __init__(self, *args, **kwargs):
        super(PointCloudMesher, self).__init__(MeshDoubleBuffer(), *args, **kwargs)

        self._loader.load()  # Sometimes needed to calculate the array shape
        self._loader.stop_loading()  # We want to start the loader from our child process so we can join it
        self._loader.reset()
        self._buffer.initialize(self._loader.get_array_ctypes(),
                                self._loader.get_array_shapes())

    @property
    def time_range(self):
        return self._loader.time_range

    def get_times(self):
        return self._loader.get_times()

    # From LoaderGenerator

    def _on_load(self, loaded_next, target_buffer):
        # Point cloud
        num_points = loaded_next[0].shape[0]
        num_allowed_points = self.get_array_shapes()[0][0]
        if num_points > num_allowed_points:
            print(self.__class__.__name__ + ' Warning: buffer can only hold ' +
                  str(num_allowed_points) + ' of the ' + str(num_points) +
                  ' points in the cloud!')
        num_points = min(num_points, num_allowed_points)
        self._buffer.get_num_points(target_buffer).value = num_points
        # This is the section which assumes exactly two arrays in the point cloud part
        np.copyto(self._buffer.get_point_cloud(target_buffer)[0][:num_points],
                  loaded_next[0][:num_points])
        np.copyto(self._buffer.get_point_cloud(target_buffer)[1][:num_points],
                  loaded_next[1][:num_points])

        # Mesh
        num_vertices = loaded_next[2].shape[0]
        num_allowed_vertices = self.get_array_shapes()[1][0]
        if num_vertices > num_allowed_vertices:
            print(self.__class__.__name__ + ' Warning: buffer can only hold ' +
                  str(num_allowed_vertices) + ' of the ' + str(num_vertices) +
                  ' vertices in the mesh!')
        num_vertices = min(num_vertices, num_allowed_vertices)
        self._buffer.get_num_vertices(target_buffer).value = num_vertices
        np.copyto(self._buffer.get_mesh(target_buffer)[0][:num_vertices],
                  loaded_next[2][:num_vertices])
        np.copyto(self._buffer.get_mesh(target_buffer)[1][:num_vertices],
                  loaded_next[3][:num_vertices])
        num_faces = loaded_next[4].shape[0]
        num_allowed_faces = self.get_array_shapes()[2][0]
        if num_faces > num_allowed_faces:
            print(self.__class__.__name__ + ' Warning: buffer can only hold ' +
                  str(num_allowed_faces) + ' of the ' + str(num_faces) +
                  ' faces in the mesh!')
        num_faces = min(num_faces, num_allowed_faces)
        self._buffer.get_num_faces(target_buffer).value = num_faces
        np.copyto(self._buffer.get_mesh(target_buffer)[2][:num_faces],
                  loaded_next[4][:num_faces])
        return None

    def _process_result(self, result):
        # Point cloud
        num_points = self._buffer.num_current_points.value
        arrays = [array[:num_points] for array in self._buffer.current_point_cloud]

        # Mesh
        num_vertices = self._buffer.num_current_vertices.value
        num_faces = self._buffer.num_current_faces.value
        mesh = self._buffer.current_mesh
        arrays.extend([mesh[0][:num_vertices], mesh[1][:num_vertices], mesh[2][:num_faces]])
        return arrays

    def reset(self):
        super(PointCloudMesher, self).reset()
        self._loader.reset()

    # From ArraysSource

    def get_array_ctypes(self):
        return self._loader.get_array_ctypes()

    def get_array_shapes(self):
        return self._loader.get_array_shapes()
