"""Classes representing point clouds."""
import multiprocessing
import ctypes
import operator

import scipy.io
import numpy as np

from utilities import util, parallelism
import arrays

class PointCloud(arrays.ArraysSource):
    def __init__(self):
        self.points = None
        self.colors = None

    def load_from_mat(self, path):
        cloud = scipy.io.loadmat(path)['S'].T
        self.points = cloud[:, :3]
        self.colors = cloud[:, 3:]

    @property
    def num_points(self):
        return self.points.shape[0]

    # From ArraysSource

    @property
    def array_ctypes(self):
        return (ctypes.c_double, ctypes.c_double)

    @property
    def array_shapes(self):
        return (self.points.shape, self.colors.shape)

class Sequence(object):
    """Interface for point cloud sequences."""

    @property
    def num_points(self):
        return None

# PARALLEL LOADING

class SynchronizedBuffer(object):
    def __init__(self, num_components=2):
        self.lock = multiprocessing.RLock()
        self.num_points = multiprocessing.Value(ctypes.c_int, 0, lock=self.lock)
        self.__shared_bases = [None for _ in range(num_components)]
        self.point_properties = [None for _ in range(num_components)]

    def initialize(self, ctypes, shapes):
        self.__shared_bases = [
            multiprocessing.Array(ctype, reduce(operator.mul, shape, 1), lock=self.lock)
            for (base, ctype, shape) in zip(self.__shared_bases, ctypes, shapes)
        ]
        self.point_properties = [np.ctypeslib.as_array(base.get_obj()).reshape(*shape)
                                 for (base, shape) in zip(self.__shared_bases, shapes)]

class DoubleBuffer(parallelism.DoubleBuffer):
    def __init__(self, num_components=2):
        super(DoubleBuffer, self).__init__()
        self._point_clouds = [SynchronizedBuffer(num_components),
                              SynchronizedBuffer(num_components)]

    def initialize(self, ctypes, shapes):
        for point_cloud in self._point_clouds:
            point_cloud.initialize(ctypes, shapes)

    # From parallelism.DoubleBuffer

    def get_buffer(self, buffer_id):
        return self._point_clouds[buffer_id]

class ParallelLoader(parallelism.LoaderGeneratorProcess):
    """Generates point clouds sequentially in a separate process into shared memory."""
    def __init__(self, PointCloudLoaderGeneratorFactory, *args, **kwargs):
        super(ParallelLoader, self).__init__(
            PointCloudLoaderGeneratorFactory, DoubleBuffer, *args, **kwargs)

        self.loader.load()  # Sometimes needed to calculate the array shape
        self.loader.stop_loading()  # We want to start the loader from our child process so we can join it
        self.loader.reset()
        self.double_buffer.initialize(self.loader.array_ctypes,
                                      self.loader.array_shapes)

    @property
    def time_range(self):
        return self.loader.time_range

    def get_times(self):
        return self.loader.get_times()

    # From DoubleBufferedProcess

    def on_write_to_buffer(self, point_cloud, write_buffer):
        num_allowed_points = self.array_shapes[0][0]
        num_points = min(point_cloud.num_points, num_allowed_points)
        write_buffer.num_points.value = num_points
        util.update_list_data_buffer(
            write_buffer.point_properties[0], point_cloud.points, point_cloud.num_points)
        util.update_list_data_buffer(
            write_buffer.point_properties[1], point_cloud.colors, point_cloud.num_points)

    # From LoaderGeneratorProcess

    def unmarshal_output(self, marshalled, read_buffer):
        num_points = read_buffer.num_points.value
        point_cloud = PointCloud()
        point_cloud.points = read_buffer.point_properties[0][:num_points, :]
        point_cloud.colors = read_buffer.point_properties[1][:num_points, :]
        return point_cloud

    # From ArraySource

    @property
    def array_ctypes(self):
        return self.loader.array_ctypes

    @property
    def array_shapes(self):
        return self.loader.array_shapes

