"""Functions and classes for loading of point clouds."""
import ctypes

from data import arrays, point_clouds
import sequences

# SEQUENCE DEFINITIONS

class Sequence(sequences.FileSequence, point_clouds.Sequence):
    """A sequence of point clouds stored in discrete .mat files."""
    def __init__(self, *args, **kwargs):
        if 'suffix' not in kwargs or not kwargs['suffix'].endswith('.mat'):
            kwargs['suffix'] = '.mat'
        if 'array_name' in kwargs:
            array_name = kwargs['array_name']
            del kwargs['array_name']
        else:
            array_name = 'points'
        if 'transpose' in kwargs:
            transpose = kwargs['transpose']
            del kwargs['transpose']
        else:
            transpose = False
        super(Sequence, self).__init__(*args, **kwargs)
        self.array_name = array_name
        self.transpose = transpose
        self._num_points = None
        self._num_samples = None

    def __getitem__(self, index):
        point_cloud = point_clouds.PointCloud()
        point_cloud.load_from_mat(self.file_path(index), self.array_name,
                                  transpose=self.transpose)
        return point_cloud

    @property
    def num_points(self):
        if self._num_points is None:
            self._num_points = self[next(self.indices)].num_points
        return self._num_points

    @property
    def num_samples(self):
        if self._num_samples is None:
            self._num_samples = len(list(self.indices))
        return self._num_samples


# SEQUENCE LOADERS

class SequenceLoader(sequences.FileSequenceLoader, arrays.ArraysSource):
    def __init__(self, sequence, max_num_points=None):
        super(SequenceLoader, self).__init__(sequence)
        self.max_num_points = max_num_points

    # From ArraysSource

    @property
    def array_ctypes(self):
        return (ctypes.c_double, ctypes.c_double)

    @property
    def array_shapes(self):
        return ((self.max_num_points, 3), (self.max_num_points, 3))

class SequenceConcurrentLoader(sequences.FileSequenceConcurrentLoader, arrays.ArraysSource):
    def __init__(self, sequence, max_size=10, max_num_points=None):
        super(SequenceConcurrentLoader, self).__init__(
            sequence, max_size)
        self.max_num_points = max_num_points

    # From ArraysSource

    @property
    def array_ctypes(self):
        return (ctypes.c_double, ctypes.c_double)

    @property
    def array_shapes(self):
        return ((self.max_num_points, 3), (self.max_num_points, 3))

