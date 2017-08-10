#!/usr/bin/env python2
"""Functions and classes for loading of results output by libomnistereo."""
from os import path

import point_clouds
import datasets

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
                    'files': point_clouds.Sequence(
                        path.join(sequences_root_path, 'Rectification'),
                        prefix='point_cloud_stereo_',
                        array_name='S',
                        transpose=True
                    )
                },
                'mrf': {
                    'files': point_clouds.Sequence(
                        path.join(sequences_root_path, 'Stereo_Disp'),
                        prefix='Pointcloud_MRF',
                        array_name='points',
                        transpose=True
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
