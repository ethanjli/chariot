"""Helper functions for working with files."""
import os
import errno

import util

# FILE AND PATH ITERATION

def paths(files_directories, file_names, file_prefix='', file_suffix=''):
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
        full_file_name = file_prefix + str(file_name) + file_suffix
        if return_multiple:
            yield tuple(os.path.join(directory, full_file_name)
                        for directory in files_directories)
        else:
            yield os.path.join(files_directory, full_file_name)

def file_names(parent_path, file_prefix='', file_suffix=''):
    """A generator of file names with the specified prefix and suffix in the specified directory.
    Output is naturally sorted, so numbers are in ascending order.
    """
    for path in sorted(os.listdir(parent_path), key=util.natural_keys):
        file_name = os.path.basename(path)
        if file_name.startswith(file_prefix) and file_name.endswith(file_suffix):
            yield file_name

def file_name_roots(parent_path, file_prefix='', file_suffix=''):
    """A generator of file indices with the specified prefix and suffix in the specified directory.
    The index of a file is the filename stripped of its prefix and suffix.
    """
    for file_name in file_names(parent_path, file_prefix, file_suffix):
        yield file_name[len(file_prefix):-len(file_suffix)]

# FILE OPERATIONS

def make_dir_path(path):
    """Ensures that the path is valid, creating directories when necessary."""
    try:
        os.makedirs(path)
    except OSError as e:
        if not(e.errno == errno.EEXIST and os.path.isdir(path)):
            raise

