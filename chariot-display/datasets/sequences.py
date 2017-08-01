#!/usr/bin/env python2
"""Functions and classes for loading of data from Oxford datasets."""
from os import path

from utilities import files
from data import data, concurrent

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

    def __getitem__(self, index):
        """Returns the data at the specified index.
        Implement this."""
        return None

    @property
    def indices(self):
        """Returns a generator of file indices in ascending order."""
        return files.file_name_roots(self.parent_path, self.prefix, self.suffix)

    @property
    def file_paths(self):
        """Returns a generator of file paths in ascending index order."""
        return files.paths(self.parent_path, self.indices, self.prefix, self.suffix)

class FileSequenceLoader(data.DataLoader, data.DataGenerator):
    """Class for synchronous loading of FileSequences."""
    def __init__(self, sequence, *args, **kwargs):
        super(FileSequenceLoader, self).__init__(*args, **kwargs)
        self.sequence = sequence
        self._indices = self.sequence.indices

    def load_next(self):
        """Loads the data at the next time point specified by the indices and returns it.
        If there is no data to load, returns None."""
        index = next(self._indices, None)
        if index is None:
            return None
        else:
            return self.sequence[index]

    # From DataLoader

    def next(self):
        """Loads the data at the next time point specified by the indices and returns it.
        If there is no data to load, raises StopIteration."""
        next_data = self.load_next()
        if next_data is None:
            raise StopIteration
        return next_data

    # From DataGenerator

    def reset(self):
        """Resets the loader to start loading from the top."""
        self._indices = self.sequence.indices

    def __len__(self):
        """Returns the number of time points of data in the sequence."""
        return self.sequence.num_samples

class FileSequenceConcurrentLoader(concurrent.Loader, FileSequenceLoader):
    def __init__(self, sequence, max_size, *args, **kwargs):
        super(FileSequenceConcurrentLoader, self).__init__(max_size, sequence, *args, **kwargs)

