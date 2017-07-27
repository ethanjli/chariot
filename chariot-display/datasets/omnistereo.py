#!/usr/bin/env python2
"""Functions and classes for loading of results output by libomnistereo."""
from os import path

from data import point_clouds
import sequences
import datasets

class PointCloudSequence(sequences.FileSequence):
    """A sequence of point clouds stored in discrete .mat files."""
    def __init__(self, *args, **kwargs):
        if 'suffix' not in kwargs or not kwargs['suffix'].endswith('.mat'):
            kwargs['suffix'] = '.mat'
        super(PointCloudSequence, self).__init__(*args, **kwargs)

    def point_cloud(self, index):
        """Returns the loaded point cloud at the specified index."""
        point_cloud = point_clouds.PointCloud()
        point_cloud.load_from_mat(self.file_path(index))
        return point_cloud

    @property
    def point_clouds(self):
        """Returns a generator of PointClouds."""
        def generate_point_clouds():
            for index in self.indices:
                yield self.point_cloud(index)
        return generate_point_clouds

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
                        path.join(sequences_root_path, 'Stereo_Disp'), 'P_hor_'
                    )
                }
            }
        }

    # Implements Dataset

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
