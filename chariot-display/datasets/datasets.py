#!/usr/bin/env python2
"""Functions and classes for loading of data from datasets."""
from os import path

_DATASETS_PATH_FILENAME = "datasets_path"

_PACKAGE_PATH = path.dirname(path.dirname(path.abspath(__file__)))
_ROOT_PATH = path.dirname(_PACKAGE_PATH)

with open(path.join(_PACKAGE_PATH, _DATASETS_PATH_FILENAME), 'r') as f:
    DATASETS_PATH = f.read().replace('\n', '').strip()

class Dataset(object):
    """Interface for datasets consisting of Sequences."""
    @property
    def parent_path(self):
        """Returns the path of the parent of the dataset.
        Implement this."""
        return DATASETS_PATH

    @property
    def sequences(self):
        """Returns a dict (possibly nested) of Sequence objects.
        Implement this."""
        return {}

