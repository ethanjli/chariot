#!/usr/bin/env python2
"""Functions and classes for loading of results output by libomnistereo."""
from os import path

from data import data, asynchronous, point_clouds
import sequences
import datasets

class PointCloudSequence(sequences.FileSequence):
    """A sequence of point clouds stored in discrete .mat files."""
    def __init__(self, *args, **kwargs):
        if 'suffix' not in kwargs or not kwargs['suffix'].endswith('.mat'):
            kwargs['suffix'] = '.mat'
        super(PointCloudSequence, self).__init__(*args, **kwargs)
        self._num_points = None
        self._num_samples = None

    def point_cloud(self, index):
        """Returns the loaded point cloud at the specified index."""
        point_cloud = point_clouds.PointCloud()
        point_cloud.load_from_mat(self.file_path(index))
        return point_cloud

    @property
    def num_points(self):
        if self._num_points is None:
            first_point_cloud = self.point_cloud(next(self.indices))
            self._num_points = first_point_cloud.num_points
        return self._num_points

    @property
    def num_samples(self):
        if self._num_samples is None:
            self._num_samples = len(list(self.indices))
        return self._num_samples

class PointCloudSequenceLoader(data.DataLoader, data.DataGenerator):
    """Class for synchronous PointCloud loading."""
    def __init__(self, sequence, *args, **kwargs):
        super(PointCloudSequenceLoader, self).__init__(*args, **kwargs)
        self.sequence = sequence
        self._indices = self.sequence.indices

    def load_next(self):
        """Loads the next point cloud specified by the indices and returns it.
        If there is no point cloud to load, returns None."""
        index = next(self._indices, None)
        if index is None:
            return None
        else:
            return self.sequence.point_cloud(index)

    # From DataLoader

    def next(self):
        next_point_cloud = self.load_next()
        if next_point_cloud is None:
            raise StopIteration
        return next_point_cloud

    # From DataGenerator

    def reset(self):
        self._indices = self.sequence.indices

    def __len__(self):
        return self.sequence.num_samples

class PointCloudSequenceAsyncLoader(asynchronous.Loader, PointCloudSequenceLoader):
    def __init__(self, sequence, max_size=10, *args, **kwargs):
        super(PointCloudSequenceAsyncLoader, self).__init__(
            max_size, False, sequence, *args, **kwargs)

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
