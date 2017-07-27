#!/usr/bin/env python2
"""Classes to enable painless process-level parallelism."""

import threading
import operator
import multiprocessing
from multiprocessing import Array, Value
import ctypes
try:
        from Queue import Empty
except ImportError:
        from queue import Empty

import numpy as np
from numpy.ctypeslib import as_array

from data import data

# THREADING

class Thread(object):
    """Abstract convenience class for work done asynchronously in a thread."""
    def __init__(self):
        self._thread = None
        self._run = True

    @property
    def name(self):
        """The name of the thread.
        Override this to use something other than the name of the derived class."""
        return self.__class__.__name__

    def on_run_start(self):
        """Do any work before execute starts being called.
        Implement this."""
        pass

    def execute(self):
        """Do the work.
        Implement this with the work to be done. If the work never ends,
        it needs to check self._run to be able to be preemptively terminated.
        If the work does end, it will be called repeatedly as long as self._run is True."""
        pass

    def on_run_finish(self):
        """Do any work after execute stops being called.
        Implement this."""
        pass

    def run_sync(self):
        """Perform the work synchronously."""
        self.on_run_start()
        while self._run:
            self.execute()
        self.on_run_finish()

    def run_async(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self.run_sync, name=self.name)
        self._thread.start()

    def terminate(self):
        self.on_terminate()
        self._run = False
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self.on_terminate_finish()

    def on_terminate(self):
        """Do any work right before termination.
        Implement this."""
        pass

    def on_terminate_finish(self):
        """Do any work right after termination.
        Implement this."""
        pass

# PROCESSES

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

def flush_queue(queue):
    try:
        for item in iter(queue.get_nowait, None):
            pass
    except Empty:
        pass

class DoubleBuffer(object):
    """Abstract base class for double buffering.
    The current buffer is used for reading, while the shadow buffer is used for writing
    the next current buffer.
    Note that only the locks and event are synchronized across processes.
    """
    def __init__(self):
        self.ready = multiprocessing.Event()
        self.shadow_ready = multiprocessing.Event()
        self._buffer_id = 0
        self._buffer_locks = [multiprocessing.Lock(), multiprocessing.Lock()]

    @property
    def current_id(self):
        return self._buffer_id

    @property
    def shadow_id(self):
        return 1 - self._buffer_id

    @property
    def current_lock(self):
        return self._buffer_locks[self.current_id]

    @property
    def shadow_lock(self):
        return self._buffer_locks[self.shadow_id]

    def get_lock(self, buffer_id):
        return self._buffer_locks[buffer_id]

    def release_locks(self):
        for lock in self._buffer_locks:
            try:
                lock.release()
            except ValueError:
                pass

    def swap(self):
        self._buffer_id = 1 - self._buffer_id

    def reset(self):
        self.ready.clear()
        self.shadow_ready.clear()


class LoaderGenerator(data.DataLoader, data.DataGenerator):
    """Mix-in for producing data in a separate process with double-buffering.
    For proper multiple inheritance MRO, this should be the leftmost base class.

    Method _on_load(self, loaded_next) needs to be implemented somewhere. It should
    return some data, or None if there is no additional data to return.
    Method _process_result(self, result) needs to be implemented somewhere. It should
    return some data, or None if there is no additional data to return.
    """
    def __init__(self, double_buffer, Loader, *args, **kwargs):
        self._loader = Loader(*args, **kwargs)
        self.__loader_process = None

        # Input and output queues
        self.__loader_process_commands = multiprocessing.Queue(1)
        self.__loader_process_results = multiprocessing.Queue(1)

        self._loader_ready = multiprocessing.Event()
        self._buffer = double_buffer

    # From DataGenerator

    def next(self, block=True, timeout=1):
        self._buffer.shadow_ready.wait()
        while not self._buffer.current_lock.acquire(block, timeout):
            pass
        self._buffer.shadow_ready.clear()
        self._buffer.shadow_lock.release()
        self.__loader_process_commands.put(('load_next', self._buffer.shadow_id))

        result = self.__loader_process_results.get()
        if result['has_current']:
            processed_result = self._process_result(result['result'])
            self._buffer.swap()
            return processed_result
        else:
            raise StopIteration

    def reset(self):
        self.stop_loading()
        self._loader_ready.clear()
        self._buffer.reset()
        self._buffer.release_locks()
        flush_queue(self.__loader_process_commands)
        flush_queue(self.__loader_process_results)
        super(LoaderGenerator, self).reset()

    # From DataLoader

    def load(self):
        if self.__loader_process is not None:
            print(self.__class__.__name__ + ' Warning: Already loading. Doing nothing.')
            return
        self.__loader_process = multiprocessing.Process(
            target=self._load_next_when_requested, name=self.__class__.__name__)
        self.__loader_process.start()
        self.__loader_process_commands.put(('load_next', self._buffer.current_id))
        self._buffer.shadow_lock.acquire()
        self._loader_ready.wait()
        self._buffer.ready.wait()

    def stop_loading(self):
        if self.__loader_process is None:
            print(self.__class__.__name__ + ' Warning: Not currently loading. Doing nothing.')
            return
        print(self.__class__.__name__ + ': Stopping loading...')
        self.__loader_process_commands.put(None)
        self.__loader_process.join()
        self.__loader_process = None
        super(LoaderGenerator, self).stop_loading()

    # In the child

    def _load_next_when_requested(self, block=True, timeout=1):
        self._loader.load()
        self._loader_ready.set()
        keep_loading = True
        while True:
            while True:
                try:
                    command = self.__loader_process_commands.get(block, timeout)
                    break
                except Empty:
                    pass
            if command is None:
                break
            elif command[0] == 'load_next':
                if keep_loading:
                    keep_loading = self._load_next(command[1])
                self._buffer.ready.set()
        self._loader.stop_loading()

    def _load_next(self, buffer_id):
        with self._buffer.get_lock(buffer_id):
            keep_loading = True
            try:
                loaded_next = next(self._loader)
                output = {
                    'has_current': True,
                    'result': self._on_load(loaded_next, buffer_id)
                }
            except StopIteration:
                output = {
                    'has_current': False
                }
                keep_loading = False
            self._buffer.shadow_ready.set()
            self.__loader_process_results.put(output)
            return keep_loading

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

class ArrayLoader(LoaderGenerator, data.ArraySource):
    """Loads numpy arrays sequentially in a separate process into shared memory.
    PreloadingAsynchronousDataLoader should also implement the ArraySource interface."""
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

    def get_array_ctype(self):
        return self._loader.get_array_ctype()

    def get_array_shape(self):
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
        super(ChunkLoader, self).__init__(data.AsynchronousDataChunkLoader,
                                          *args, **kwargs)
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

class PointCloudGenerator(LoaderGenerator):
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

class PointCloudMesher(LoaderGenerator):
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
