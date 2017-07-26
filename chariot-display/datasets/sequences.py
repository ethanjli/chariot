#!/usr/bin/env python2
"""Functions and classes for loading of data from Oxford datasets."""
from os import path

from utilities import files

class Sequence(object):
    """Base class for a uniform sequence of data over time."""
    def __init__(self):
        pass

class FileSequence(Sequence):
    """Sequences for which data at each time is stored in a numbered file.
    All files should be in the same parent directory."""
    def __init__(self, parent_path, prefix='', suffix=''):
        super(FileSequence, self).__init__()
        self.parent_path = parent_path
        self.prefix = prefix
        self.suffix = suffix

    def file_name(self, index):
        """Returns the file name of the file at the specified index.
        In this class, index is passed through literally.
        """
        return ''.join([self.prefix, index, self.suffix])

    def file_path(self, *args, **kwargs):
        """Returns the path of the specified file."""
        return path.join(self.parent_path, self.file_name(*args, **kwargs))

    @property
    def indices(self):
        """Returns a generator of file indices in ascending order."""
        return files.file_name_roots(self.parent_path, self.prefix, self.suffix)

    @property
    def file_paths(self):
        """Returns a generator of file paths in ascending index order."""
        return files.paths(self.parent_path, self.indices, self.prefix, self.suffix)

