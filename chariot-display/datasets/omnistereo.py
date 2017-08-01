#!/usr/bin/env python2
"""Functions and classes for loading of results output by libomnistereo."""
from os import path
import ctypes

from data import arrays, point_clouds
import sequences
import datasets

# SEQUENCE DEFINITIONS

class PointCloudSequence(sequences.FileSequence, point_clouds.Sequence):
    """A sequence of point clouds stored in discrete .mat files."""
    def __init__(self, *args, **kwargs):
        if 'suffix' not in kwargs or not kwargs['suffix'].endswith('.mat'):
            kwargs['suffix'] = '.mat'
        super(PointCloudSequence, self).__init__(*args, **kwargs)
        self._num_points = None
        self._num_samples = None

    def __getitem__(self, index):
        point_cloud = point_clouds.PointCloud()
        point_cloud.load_from_mat(self.file_path(index))
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

class PointCloudSequenceLoader(sequences.FileSequenceLoader, arrays.ArraysSource):
    def __init__(self, sequence, max_num_points=None):
        super(PointCloudSequenceLoader, self).__init__(sequence)
        self.max_num_points = max_num_points

    # From ArraysSource

    @property
    def array_ctypes(self):
        return (ctypes.c_double, ctypes.c_double)

    @property
    def array_shapes(self):
        return ((self.max_num_points, 3), (self.max_num_points, 3))

class PointCloudSequenceConcurrentLoader(sequences.FileSequenceConcurrentLoader,
                                         arrays.ArraysSource):
    def __init__(self, sequence, max_size=10, max_num_points=None):
        super(PointCloudSequenceConcurrentLoader, self).__init__(
            sequence, max_size)
        self.max_num_points = max_num_points

    # From ArraysSource

    @property
    def array_ctypes(self):
        return (ctypes.c_double, ctypes.c_double)

    @property
    def array_shapes(self):
        return ((self.max_num_points, 3), (self.max_num_points, 3))

# DATASET DEFINITION

class Dataset(datasets.Dataset):
    """Interface for libomnistereo output datasets."""
    def __init__(self, name, parent_path=None):
        self.name = name
        self._parent_path = parent_path
        self.init_sequences()

    def init_sequences(self):
        sequences_root_path = path.join(self.parent_path, self.name, 'Seq_0008')
        self._sequences = {
            'point_cloud': {
                'raw': {
                    'files': PointCloudSequence(
                        path.join(sequences_root_path, 'Rectification'), 'point_cloud_stereo_'
                    )
                }
            }
        }

    # From datasets.Dataset

    @property
    def parent_path(self):
        """Returns the path of the parent of the dataset."""
        if self._parent_path:
            return self._parent_path
        else:
            return datasets.DATASETS_PATH

    @property
    def sequences(self):
        """Returns a dict of Sequence objects."""
        return self._sequences
