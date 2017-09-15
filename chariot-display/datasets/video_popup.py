#!/usr/bin/env python2
"""Functions and classes for loading of results output by VideoPopup."""
from os import path

import point_clouds
import datasets

# DATASET DEFINITION

class KittiDataset(datasets.Dataset):
    """Interface for VideoPopup output datasets."""
    def __init__(self, name, parent_path=None):
        self.name = name
        self._parent_path = parent_path
        self.init_sequences()

    def init_sequences(self):
        sequences_root_path = path.join(self.parent_path, self.name)
        self._sequences = {
            'point_cloud': {
                'sparse': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_sparse_',
                        array_name='points',
                        transpose=False
                    )
                },
                'dense_nearest': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_dense_nearest_',
                        array_name='points',
                        transpose=False
                    )
                },
                'dense_global': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_dense_global_',
                        array_name='points',
                        transpose=False
                    )
                },
                'dense_linear': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_dense_linear_',
                        array_name='points',
                        transpose=False
                    )
                },
                'sparse_foreground': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_foreground_',
                        array_name='points',
                        transpose=False
                    )
                },
                'dense_foreground': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_dense_foreground_',
                        array_name='points',
                        transpose=False
                    )
                },
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

class LogC920x1Dataset(datasets.Dataset):
    """Interface for VideoPopup output datasets."""
    def __init__(self, name, parent_path=None):
        self.name = name
        self._parent_path = parent_path
        self.init_sequences()

    def init_sequences(self):
        sequences_root_path = path.join(self.parent_path, self.name)
        self._sequences = {
            'point_cloud': {
                'sparse': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_sparse_',
                        array_name='points',
                        transpose=False,
                        color_type='uint8'
                    )
                },
                'dense_nearest': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_dense_nearest_',
                        array_name='points',
                        transpose=False,
                        color_type='uint8'
                    )
                },
                'dense_linear': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_dense_linear_',
                        array_name='points',
                        transpose=False,
                        color_type='uint8'
                    )
                },
                'dense_global': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_dense_global_',
                        array_name='points',
                        transpose=False,
			color_type = 'uint8'
                    )
                },
                'sparse_foreground': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_foreground_',
                        array_name='points',
                        transpose=False,
                        color_type='uint8'
                    )
                },
                'dense_foreground': {
                    'files': point_clouds.Sequence(
                        sequences_root_path,
                        prefix='points_dense_foreground_',
                        array_name='points',
                        transpose=False,
                        color_type='uint8'
                    )
                },
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
