#!/usr/bin/env python2
"""Functions and classes for loading of data from Oxford datasets."""
from os import path
import numpy as np

from utilities import util
import image_loading

_DATASETS_PATH_FILENAME = "datasets"

_PACKAGE_PATH = path.dirname(path.dirname(path.abspath(__file__)))
_ROOT_PATH = path.dirname(_PACKAGE_PATH)

with open(path.join(_PACKAGE_PATH, _DATASETS_PATH_FILENAME), 'r') as f:
    DATASETS_PATH = f.read().replace('\n', '').strip()

SEQUENCE_LOCATIONS = {
    'stereo': ['left', 'right', 'centre'],
    'stereo_preprocessed': ['left', 'right', 'centre'],
    'stereo_preprocessed_chunked': ['left', 'right', 'centre'],
    'mono': ['left', 'right', 'rear'],
    'mono_preprocessed': ['left', 'right', 'rear'],
    'mono_preprocessed_chunked': ['left', 'right', 'rear'],
    'lms': ['front', 'rear'],
    'lms_preprocessed': ['front', 'rear'],
    'ldmrs': None,
    'vo': None,
    'vo_preprocessed': ['pose', 'xyzrpy']
}

SEQUENCE_SUFFIXES = {
    'stereo': '.png',
    'stereo_preprocessed': '.png',
    'stereo_preprocessed_chunked': '.h5',
    'mono': '.png',
    'mono_preprocessed': '.png',
    'mono_preprocessed_chunked': '.h5',
    'lms': '.bin',
    'lms_preprocessed': '.h5',
    'ldmrs': '.bin',
    'vo': '.csv',
    'vo_preprocessed': '.csv',
    'vo_preprocessed_xyzrpy': '.csv'
}


# TIME SEQUENCING

ITERS_PER_SECOND = 1000000


# PATH FINDING

def get_sequence_name(sequence, namespace=None):
    """Returns the name of a sensor sequence.
    Useful to get the path of a sensor sequence or its timestamp filename.
    Performs no error-checking.

    Args:
        sequence: either the name of a single-sensor sequence set (e.g. 'ldmrs')
        or a pair of the name of the sequence set and the sensor location
        (e.g. ('stereo', 'left'))
        namespace: if set to 'file', the stereo sequence set is treated as a
        multi-sensor sequence. Only relevant when sequence == 'stereo'.
    """
    if (sequence == 'ldmrs' or sequence == 'vo' or
            (namespace != 'file' and (sequence == 'stereo' or
                                      sequence == 'stereo_preprocessed' or
                                      sequence == 'stereo_preprocessed_chunked'))):
        return sequence
    elif isinstance(sequence, tuple):
        if namespace == 'file':
            return path.join(*sequence)
        if (sequence[0] == 'lms_preprocessed' or
                sequence[0] == 'stereo_preprocessed_chunked'):
            return sequence[0] + '_' + sequence[1] + SEQUENCE_SUFFIXES[sequence[0]]
        return sequence[0] + '_' + sequence[1]
    return None

def get_sequence_suffix(sequence):
    """Returns the filetype suffix for files of the specified sequence.

    Args:
        sequence: either the name of a single-sensor sequence set (e.g. 'ldmrs')
        or a pair of the name of the sequence set and the sensor location
        (e.g. ('stereo', 'left'))
    """
    if isinstance(sequence, str):
        return SEQUENCE_SUFFIXES[sequence]
    return SEQUENCE_SUFFIXES[sequence[0]]

def get_oxford_dataset_path(dataset_id):
    """Returns the path of the Oxford dataset directory.

    Args:
        dataset_id: the id of the dataset (i.e. a set of sensor sequences)
    """
    return path.join(DATASETS_PATH, 'oxford', dataset_id)

def get_oxford_sequence_paths(dataset_id, sequence_set):
    """Returns a tuple of all directory paths for a sequence set of the given dataset.

    Args:
        dataset_id: the id of the dataset (i.e. a set of sensor sequences)
        sequence_set: the name of a set of sensor sequences. Options: 'stereo',
        'stereo_preprocessed', 'mono', 'mono_preprocessed', 'lms', 'ldmrs'.
    """
    locations = SEQUENCE_LOCATIONS[sequence_set]
    dataset_path = get_oxford_dataset_path(dataset_id)
    if (sequence_set == 'ldmrs' or sequence_set == 'vo'):
        return tuple({path.join(dataset_path, get_sequence_name(sequence_set))})
    if sequence_set == 'stereo' or sequence_set == 'stereo_preprocessed' or sequence_set == 'vo_preprocessed':
        namespace = 'file'
    else:
        namespace = None
    paths = tuple(path.join(dataset_path,
                            get_sequence_name((sequence_set, location), namespace))
                  for location in locations)
    return paths


# DATA FILE LOADING

'''Returns the raw lidar data points in the image

Args:
 pose:  pose file for the given timestamp
 G_posesource_laser: the location of the laser relative to pose
'''
def load_lidar_raw(lidar_path):
   # print(lidar_path)

    if not path.isfile(lidar_path):
        raise IOError('Lidar file does not exist')

    scan_file = open(lidar_path)
    scan = np.fromfile(scan_file, np.double)
    scan_file.close()

    scan = scan.reshape((len(scan) // 3, 3)).transpose()

    return scan

def process_lidar(scan, pose, G_posesource_laser=np.eye(4, dtype=np.float32)):


#   # TODO: make this work for ldmrs as well as lms_front
#    if lidar != 'ldmrs':
        # LMS scans are tuples of (x, y, reflectance)
    reflectance = np.ravel(scan[2, :])
    scan[2, :] = np.zeros((1, scan.shape[1]))


    transform = np.dot(pose, G_posesource_laser)
    scan_homogenous = np.vstack([scan, np.ones((1, scan.shape[1]))])

    pointcloud = np.dot(transform, scan_homogenous)
    pointcloud = np.transpose(pointcloud[:3, :])

    if pointcloud.shape[1] == 0:
        raise IOError("Could not find scan files for given time range in directory " + lidar_dir)
    return (pointcloud, reflectance)


def get_extrinsics(sequence, cache={}):
    """Returns the camera model for the corresponding sequence.
    This function is memoized.

    Args:
        sequence: a pair of the name of the sequence set and the sensor location. Options:
        'stereo', ('mono', 'left'), ('mono', 'right'), ('mono', 'rear'),
        ('mono_preprocessed', 'left'), ('mono_preprocessed', 'right'),
        ('mono_preprocessed', 'rear'), 'ins', 'ldmrs', ('lms', 'front'), ('lms', 'rear').
    """
    if sequence in cache:
        extrinsics = cache[sequence]
    else:
        with open(path.join(_EXTRINSICS_PATH, get_sequence_name(sequence) + '.txt')) as f:
            line = f.read().replace('\n', '').strip()
            extrinsics = [float(x) for x in line.split(' ')]
        cache[sequence] = extrinsics

    return extrinsics

# DATASET LOADING

def get_timestamps_path(dataset_id, name):
    """Returns the full path of the timestamps file for the specified dataset and filename.

    Args:
        dataset_id: the id of the dataset (i.e. a set of sensor sequences)
        name: the file name, without file suffix. Options: 'ldmrs', 'lms_front',
        'lms_rear', 'mono_left', 'mono_rear', 'mono_right', 'mono_preprocessed_left',
        'mono_preprocessed_rear', 'mono_preprocessed_right', 'stereo', 'stereo_preprocessed'.
    """
    return path.join(get_oxford_dataset_path(dataset_id), name + '.timestamps')

def load_timestamps(dataset_id, name):
    """Returns a list of timestamps of the specified dataset and timestamps filename.

    Args:
        dataset_id: the id of the dataset (i.e. a set of sensor sequences)
        name: the file name, without file suffix. Options: 'ldmrs', 'lms_front',
        'lms_rear', 'mono_left', 'mono_rear', 'mono_right', 'mono_preprocessed_left',
        'mono_preprocessed_rear', 'mono_preprocessed_right', 'stereo', 'stereo_preprocessed'.
    """
    file_path = get_timestamps_path(dataset_id, name)
    with open(file_path, 'r') as f:
        lines = f.readlines()
    timestamps = [l.split(' ')[0] for l in lines]
    #timestamps = [l.strip().split()[0] for l in lines]
    return timestamps

class Dataset():
    """A class to help with loading of data from Oxford datasets."""
    def __init__(self, dataset_id, load_preprocessed=False):
        self.dataset_id = dataset_id

        #Less efficient, but it needs the extra case
        self.paths = dict()
        for sequence_set in SEQUENCE_LOCATIONS.keys():
            if SEQUENCE_LOCATIONS[sequence_set] is None:
                self.paths[sequence_set] = get_oxford_sequence_paths(dataset_id, sequence_set)
            else:
                self.paths[sequence_set] = dict(zip(SEQUENCE_LOCATIONS[sequence_set],
                                   get_oxford_sequence_paths(dataset_id, sequence_set)))

        self._timestamps = {
            'stereo': load_timestamps(dataset_id, 'stereo'),
            'mono': {location: load_timestamps(dataset_id,
                                               get_sequence_name(('mono', location)))
                     for location in SEQUENCE_LOCATIONS['mono']},
            'lms': {location: load_timestamps(dataset_id,
                                              get_sequence_name(('lms', location)))
                    for location in SEQUENCE_LOCATIONS['lms']},
            'ldmrs': load_timestamps(dataset_id, 'ldmrs')
        }
        if load_preprocessed:
            self._timestamps['stereo_preprocessed'] = \
                    load_timestamps(dataset_id, 'stereo_preprocessed')
            self._timestamps['mono_preprocessed'] = {
                location: load_timestamps(dataset_id,
                                          get_sequence_name(('mono_preprocessed', location)))
                for location in SEQUENCE_LOCATIONS['mono_preprocessed']
            }

    def get_odometry_file(self, sequence='vo'):
        return path.join(self.get_dir(sequence), 'vo.csv')

    def get_dir(self, name):
        return path.join(get_oxford_dataset_path(self.dataset_id), name)

    def get_path(self, sequence):
        """Returns the files directory path for the specified sensor sequence."""
        return util.get_from_tree(self.paths, sequence)

    def get_timestamps_path(self, sequence):
        if isinstance(sequence, tuple) and (sequence[0] == 'stereo'
                                            or sequence[0] == 'stereo_preprocessed'
                                            or sequence[0] == 'stereo_preprocessed_chunked'):
            sequence = sequence[0]
        return get_timestamps_path(self.dataset_id, get_sequence_name(sequence))

    def get_timestamps(self, sequence):
        """Returns the timestamps for the specified sensor sequence."""
        if isinstance(sequence, tuple) and (sequence[0] == 'stereo'
                                            or sequence[0] == 'stereo_preprocessed'):
            sequence = sequence[0]
        return [int(time) for time in util.get_from_tree(self._timestamps, sequence)]

    def count_timestamps(self, sequence):
        """Returns the number of timestamps for the specified sensor sequence."""
        return len(self.get_timestamps(sequence))

    def get_time_range(self, sequence, time_range=None):
        """Returns the start time, end time, and time duration of the specified sequence."""
        timestamps = self.get_timestamps(sequence)
        if time_range is None:
            return util.TimeRange(0, timestamps[-1] - timestamps[0], timestamps[0])
        if time_range.reference is None:
            time_range.reference = timestamps[0]
        return time_range

    def get_image_shape(self, sequence, downsampling=1, cache={}):
        """Returns the image dimensions of the specified sequence as a numpy array."""
        if sequence in cache:
            shape = cache[sequence]
        else:
            image_sequence = self.sequence_by_index(sequence, indices=[0])
            first_image_path = next(image_sequence)
            first_image = image_loading.load_image(first_image_path, downsampling)
            shape = first_image.shape[0:2]
            cache[sequence] = shape
        return shape

    def sequence_by_timestamp(self, sequence, time_range=None):
        """ Returns a generator of file paths in the specified time range
        Default is the entire range within the sequence diretory.
        """
        files_directory = self.get_path(sequence)

        timestamps = self.get_timestamps(sequence)
        (absolute_start, absolute_end) = self.get_time_range(sequence, time_range).absolute

        selected_timestamps = list(util.time_range_sequence(
            timestamps, absolute_start, absolute_end))
        return (util.paths_by_index(files_directory, get_sequence_suffix(sequence),
                                    selected_timestamps), iter(selected_timestamps))

    def stereo_sequences_by_timestamp(self, preprocessed=True, include_center=False,
                                      time_range=None):
        """Returns a generator of stereo file paths of specified indices.
        For each index, the generator will yield a tuple of the file paths.

        Args:
            include_center: whether the generator should include the center
            stereo camera as the third element of the yielded tuples.
            indices: an iterable collection of indices of files. If None, the entire
            sequence will be traversed.
        """
        sequence = 'stereo'
        if preprocessed:
            sequence += '_preprocessed'
        if include_center:
            locations = SEQUENCE_LOCATIONS[sequence]
        else:
            locations = SEQUENCE_LOCATIONS[sequence][0:2]
        directories = tuple(self.get_path((sequence, location)) for location in locations)

        timestamps = self.get_timestamps(sequence)
        (absolute_start, absolute_end) = self.get_time_range(
            (sequence, locations[0]), time_range).absolute

        selected_timestamps = list(util.time_range_sequence(
            timestamps, absolute_start, absolute_end))
        return (util.paths_by_index(directories, get_sequence_suffix(sequence),
                                    selected_timestamps), iter(selected_timestamps))


    def sequence_by_index(self, sequence, indices=None):
        """Returns a generator of file paths of specified indices from the specified sequence.

        Args:
            sequence: either the name of a single-sensor sequence set (e.g. 'ldmrs')
            or a pair of the name of the sequence set and the sensor location
            (e.g. ('stereo', 'left'))
            indices: an iterable collection of indices of files. If None, the entire
            sequence will be traversed.
        """
        files_directory = self.get_path(sequence)
        timestamps = self.get_timestamps(sequence)
        selected_timestamps = util.sequence(timestamps, indices)
        return util.paths_by_index(files_directory, get_sequence_suffix(sequence),
                                   selected_timestamps)

    def stereo_sequences_by_index(self, preprocessed=True, include_center=False, indices=None):
        """Returns a generator of stereo file paths of specified indices.
        For each index, the generator will yield a tuple of the file paths.

        Args:
            include_center: whether the generator should include the center
            stereo camera as the third element of the yielded tuples.
            indices: an iterable collection of indices of files. If None, the entire
            sequence will be traversed.
        """
        sequence = 'stereo'
        if preprocessed:
            sequence += '_preprocessed'
        if include_center:
            locations = SEQUENCE_LOCATIONS[sequence]
        else:
            locations = SEQUENCE_LOCATIONS[sequence][0:2]
        directories = tuple(self.get_path((sequence, location)) for location in locations)
        timestamps = self.get_timestamps(sequence)
        selected_timestamps = util.sequence(timestamps, indices)
        return util.paths_by_index(directories, get_sequence_suffix(sequence),
                                   selected_timestamps)

