#!/usr/bin/env python2
"""Generic utility functions."""
import os
import errno
import re

import numpy as np

# CONTAINERS

def get_from_tree(tree, keys):
    """Returns the value in a nested dict from walking down along the specified keys.

    Args:
        tree: a nested dict.
        keys: an iterable of the keys to follow. If keys is a string, uses keys as a single key.
    """
    cursor = tree
    if isinstance(keys, str):
        return cursor[keys]
    for key in keys:
        cursor = cursor[key]
    return cursor

class RingBuffer(object):
    """A 1-D ring buffer."""
    def __init__(self, length, dtype='f'):
        if length == 0:
            raise ValueError('RingBuffer length must be a positive number!')
        self.data = np.zeros(length, dtype=dtype)
        self._index = -1
        self.length = 0

    def reset(self):
        self.data = np.zeros(self.data.shape[0], dtype=self.data.dtype)
        self._index = -1
        self.length = 0

    def append(self, value):
        """Adds a value to the buffer, overwriting a stale entry if needed."""
        if self.length < self.data.size:
            self.length += 1
        self._index = (self._index + 1) % self.data.size
        self.data[self._index] = value

    def get_head(self):
        """Gets the most recently added value in the buffer."""
        return self.data[self._index]

    def get_tail(self):
        """Gets the least recently added value in the buffer."""
        if self.length:
            return self.data[(self._index + 1) % self.length]
        else:
            return None

    def get_continuous(self):
        """Returns a copy of the buffer with elements in correct time order."""
        if self.length < self.data.size:
            return np.concatenate((self.data[:self._index + 1],
                                   self.data[self._index + 1:]))[:self.length]
        else:
            return np.concatenate((self.data[self._index + 1:],
                                   self.data[:self._index + 1]))

def grid_data_to_list_data(data):
    """Reshapes data shaped as a grid (as in an image) to a list array, one row per grid cell."""
    return data.reshape(data.shape[0] * data.shape[1], data.shape[2])

def update_list_data_buffer(list_data_buffer, new_list_data, previous_list_data_size):
    previous_list_data_size = min(previous_list_data_size, list_data_buffer.shape[0])
    list_data_size = new_list_data.shape[0]
    if list_data_size > list_data_buffer.shape[0]:
        print('Warning: Can only add ' + str(list_data_buffer.shape[0]) + ' of the ' +
              str(list_data_size) + ' requested items!')
        new_list_data = new_list_data[:list_data_buffer.shape[0]]
    np.copyto(list_data_buffer[:list_data_size], new_list_data)
    if previous_list_data_size > list_data_size:
        list_data_buffer[list_data_size:previous_list_data_size] = \
            np.zeros((previous_list_data_size - list_data_size, new_list_data.shape[1]))

class TimeRange:
    def __init__(self, start=None, end=None, reference=None, duration=None):
        if duration is not None:
            if start is None:
                start = end - duration
            elif end is None:
                end = start + duration
        self.start = start
        self.end = end
        self.reference = reference

    @property
    def absolute(self):
        return (self.start + self.reference, self.end + self.reference)

    @property
    def duration(self):
        return self.end - self.start

    def __repr__(self):
        return 'TimeRange({},{},{})'.format(
            self.start, self.end, self.reference)


# NATURAL SORTING

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    """Used for sorting in natural order.
    From http://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return [atoi(c) for c in re.split('(\d+)', repr(text))]


# GENERATORS

def sequence(indexable, indices=None):
    """A generator walking through an indexable collection of items.

    Args:
        indexable: a collection which can be indexed by number through square brackets
        and for which len(indexable) is defined.
        indices: an iterable collection of indices into indexable. If None, the entire
        collection will be walked through.
    """
    if indices is None:
        indices = range(len(indexable))
    for index in indices:
        yield indexable[index]

def time_immediate_sequence(times, begin=0, end=None, yield_index=False):
    """A coroutine walking through an iterable sequence of times.
    Times are assumed to be monotonically non-decreasing.

    Args:
        times: an iterable collection of times.
        begin: the beginning time of the sequence range
        end: the end time of the sequence range (NOTE: defaults to entire range if no range specified)
    Coroutine Yields:
        Yields each immediate timestamp from begin to end, inclusive

    """
    index = 0
    for time in times:
        if int(time) >= begin:
            if yield_index:
                yield (index, time)
            else:
                yield time
        if end is not None and int(time) > end:
            raise StopIteration
        index += 1

def time_aligned_sequence(times, reference_times, yield_index=False):
    """A coroutine walking through an iterable sequence of times nearest to the provided reference.
    Times are assumed to be monotonically non-decreasing.

    Args:
        times: an iterable collection of times.
        reference_times: an iterable of the provided reference times.
    Coroutine Yields:
        Yields each immediate timestamp from begin to end, inclusive

    """
    index = 0
    current_reference = next(reference_times)
    for time in times:
        while int(time) >= current_reference:
            if yield_index:
                yield (index, time)
            else:
                yield time
            current_reference = next(reference_times)
        index += 1

def time_sequence(times):
    """A coroutine walking through an indexable collection of times.

    Args:
        times: an indexable collection of times.

    Coroutine Args:
        Initialize by sending None.
        Then send the end of the next time interval of timestamps to yield.
    Coroutine Yields:
        Yields a list of timestamps within the next specified time interval
        after the previous time interval.

    """
    index = 0
    next_times = []
    while True:
        next_time_limit = yield next_times
        next_times = []
        if index >= len(times):
            raise StopIteration
        while index < len(times) and times[index] <= next_time_limit:
            next_times.append(times[index])
            index += 1

def paths_by_index(files_directories, file_suffix, file_names):
    """A generator of file paths of the specified names in the specified directories.
    If multiple source directories are specified, paths of the same name in each
    directory will be yielded together in a tuple with the same order in which
    the directories were specified. Otherwise, a single path will be yielded as a string.

    Args:
        files_directories: an iterable of paths to the directories containing the files.
        If files_directory is a string, uses files_directory as a single directory.
        Note that, if files_directories consists of multiple paths, those directories
        need to have files of the same names.
        file_suffix: filename suffix for the files
        file_names: an iterable collection of file names, without the file suffix
    """
    return_multiple = True
    if isinstance(files_directories, str):
        files_directory = files_directories
        return_multiple = False
    for file_name in file_names:
        if return_multiple:
            yield tuple(os.path.join(directory, str(file_name) + file_suffix)
                        for directory in files_directories)
        else:
            yield os.path.join(files_directory, str(file_name) + file_suffix)

# FILE OPERATIONS

def make_dir_path(path):
    """Ensures that the path is valid, creating directories when necessary."""
    try:
        os.makedirs(path)
    except OSError as e:
        if not(e.errno == errno.EEXIST and os.path.isdir(path)):
            raise
