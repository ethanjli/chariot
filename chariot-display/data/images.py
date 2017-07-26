import warnings
import ctypes

import numpy as np
import scipy.misc
import skimage
import skimage.transform

from utilities import util
import data

# Image Loading Functions

def load_image(image_path, downsampling=1, downsampling_mode='downscale_local_mean'):
    """Loads an image from path as a numpy array. Downsamples by the specified power of 2.

    Args:
        downsampling: an integer factor by which to reduce the image size.
        downsampling_mode: the name of the skimage function to use. Options:
        'rescale' (fast) or 'downscale_local_mean' (accurate)
    """
    image = scipy.misc.imread(image_path)
    if downsampling == 1:
        rescaled = image
    elif downsampling_mode == 'rescale':
        rescaled = skimage.transform.rescale(image, 1.0 / downsampling, mode='constant')
    elif downsampling_mode == 'downscale_local_mean':
        rescaled = skimage.transform.downscale_local_mean(
            skimage.img_as_float(image), (downsampling, downsampling, 1))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        rescaled = skimage.img_as_ubyte(rescaled)
    return rescaled

# Image Sequence Loading Classes

class ImageLoader(data.DataLoader, data.DataGenerator):
    """Abstract base class for various image loaders.
    Image loaders load images into memory and allow images to be retrieved from memory."""
    def __init__(self, all_file_paths, downsampling):
        self._load = True
        self._all_file_paths = all_file_paths
        self._file_paths_generator = iter(self._all_file_paths)
        self.downsampling = downsampling

    def _load_next(self):
        """Loads the next image specified by the generator into memory and returns it.
        If there is no image to load, returns None.
        """
        file_paths = next(self._file_paths_generator, None)
        if file_paths is None:
            self._load = False
            return None
        if isinstance(file_paths, tuple):
            images = [load_image(file_path, self.downsampling) for file_path in file_paths]
        else:
            images = [load_image(file_paths, self.downsampling)]
        return images

    # From DataLoader
    def next(self):
        next_image = self._load_next()
        if next_image is None:
            raise StopIteration

    # From DataGenerator

    def reset(self):
        """Resets the image loader.
        The next image returned from memory should be the first one in the sequence."""
        self._file_paths_generator = iter(self._all_file_paths)

    def __len__(self):
        return len(self._all_file_paths)

class PreloadingImageLoader(ImageLoader):
    """Loads all specified images into RAM and allows fast sequential retrieval.
    Images are saved in RAM upon retrieval for later retrieval.
    Caution: if you load too many images, you may crash the system.
    """
    def __init__(self, file_paths_generator, downsampling=2):
        all_file_paths = list(file_paths_generator)
        super(PreloadingImageLoader, self).__init__(all_file_paths, downsampling)
        self._images = None
        self._all_images = None

    # From DataLoader

    def load(self):
        if self._all_images is not None:
            print('PreloadingImageLoader: Images are already loaded into memory. Doing nothing.')
            return
        super(PreloadingImageLoader, self).reset()
        num_images = len(self._all_file_paths)
        print('PreloadingImageLoader: Loading ' + str(num_images) + ' images...')
        if num_images > 500:
            print('PreloadingImageLoader Warning: Loading this many images may fill your RAM, proceed with care!')
        self._all_images = [self._load_next() for _ in range(num_images)]
        self._images = iter(self._all_images)

    # From DataGenerator

    def reset(self):
        if self._all_images is None:
            print('PreloadingImageLoader Warning: Nothing to reset. Doing nothing.')
            return  # Nothing to reset
        self._images = iter(self._all_images)

    def next(self):
        if self._all_images is None:
            raise RuntimeError('PreloadingImageLoader Error: You need to call the load method first!')
        return next(self._images)

class AsynchronousImageLoader(data.AsynchronousDataLoader, ImageLoader):
    """Loads all specified images into RAM in a separate thread.
    Note that, because image loading is slow, this gives only a small performance boost.
    """
    def __init__(self, file_paths_generator, downsampling=2, max_size=500):
        all_file_paths = list(file_paths_generator)
        super(AsynchronousImageLoader, self).__init__(max_size, discard_upon_none=False,
                                                      all_file_paths=all_file_paths, downsampling=downsampling)

class PreloadingAsynchronousImageLoader(data.PreloadingAsynchronousDataLoader, ImageLoader):
    """Blocks in the parent thread until the images buffer in the RAM is initially filled.
    This behaves like the PreloadingImageLoader but doesn't require that all files be loaded in RAM.

    Note that, because image loading is slow, performance will eventually degrade
    to that of AsynchronousImageLoader - we just get a faster start.
    """
    def __init__(self, file_paths_generator, downsampling=2, max_size=500):
        all_file_paths = list(file_paths_generator)
        super(PreloadingAsynchronousImageLoader, self).__init__(
            max_size, all_file_paths, downsampling)

class ChunkedImageLoader(data.DataLoader, data.DataGenerator):
    def __init__(self, archive_paths, indices, downsampling=1,
                 ChunkLoader=data.DataChunkLoader, *args, **kwargs):
        self._chunk_loaders = data.SynchronizedDataChunkLoaders(
            archive_paths, lazy=True, ChunkLoader=ChunkLoader,
            *args, **kwargs)
        self._chunks = None
        self._chunks_data = None
        self._all_indices = list(indices)
        self._indices = iter(self._all_indices)
        self.downsampling = downsampling

    def _get_attrs(self):
        if self._chunk_loaders.lazy:
            return self._chunks[0].attrs
        else:
            return self._chunks[0][0].attrs

    def _advance_chunks_to(self, index):
        if index < self._get_attrs()['id']:
            raise ValueError('ChunkedImageLoader: requested index is before the current chunk!',
                             index, self._get_attrs()['id'])
        while index >= (self._get_attrs()['id'] + 1) * self._get_attrs()['size']:
            self._chunks = next(self._chunk_loaders)
            self._chunks_data = None
        if self._chunks_data is None:
            self._chunks_data = [data.load_chunk_array(chunk) if self._chunk_loaders.lazy else chunk[1]
                                 for chunk in self._chunks]

    # From DataLoader

    def load(self):
        self._chunk_loaders.load()
        self._chunks = next(self._chunk_loaders)
        if self.downsampling != self._get_attrs()['downsampling']:
            raise ValueError('Chunk archive(s) have chunks with a different downsampling factor!',
                             self._get_attrs()['downsampling'], self.downsampling)

    def stop_loading(self):
        self._chunk_loaders.stop_loading()

    # From DataGenerator

    def reset(self):
        self._chunk_loaders.reset()
        self._chunks_data = None
        self._indices = iter(self._all_indices)

    def next(self):
        index = next(self._indices)
        self._advance_chunks_to(index)
        local_index = index - self._get_attrs()['id'] * self._get_attrs()['size']
        return [chunk_data[local_index] for chunk_data in self._chunks_data]

class ImageLoaderClient(data.DataLoader, data.DataGenerator, data.ArraySource):
    def __init__(self, dataset, sequences, time_range=None, reference_timestamps=None,
                 downsampling=2, ImageLoader=AsynchronousImageLoader,
                 ChunkLoader=data.DataChunkLoader):
        self._dataset = dataset
        self.sequences = sequences
        self.load_preprocessed = sequences[0][0].endswith('preprocessed')
        self.downsampling = downsampling

        time_range = dataset.get_time_range(sequences[0], time_range)
        self.time_range = time_range
        self.reference_timestamps = reference_timestamps
        if issubclass(ImageLoader, ChunkedImageLoader):
            self._init_chunked_image_loader(ImageLoader, ChunkLoader)
        elif issubclass(ImageLoader, ImageLoader):
            self._init_image_loader(ImageLoader)

    def _init_chunked_image_loader(self, ChunkedImageLoader, ChunkLoader):
        if self.sequences[0][0].startswith('stereo'):
            sequence_set = self.sequences[0][0]
            timestamps = self._dataset.get_timestamps(sequence_set)
            sequence_set += '_chunked'

            (time_begin, time_end) = self.time_range.absolute
            indices_timestamps = util.time_immediate_sequence(
                timestamps, time_begin, time_end, yield_index=True, )
            (indices, self._timestamps) = zip(*indices_timestamps)

            paths = tuple(self._dataset.get_path((sequence_set, specific_sequence))
                          for (_, specific_sequence) in self.sequences)
        else:
            timestamps = self._dataset.get_timestamps(self.sequences[0])
            indices_timestamps = util.time_aligned_sequence(
                timestamps, iter(self.reference_timestamps), yield_index=True)
            (indices, self._timestamps) = zip(*indices_timestamps)
            paths = tuple(self._dataset.get_path((sequence[0] + '_chunked', sequence[1]))
                          for sequence in self.sequences)

        self._image_loader = ChunkedImageLoader(
            paths, indices, self.downsampling, ChunkLoader=ChunkLoader)

    def _init_image_loader(self, ImageLoader):
        if self.sequences[0][0].startswith('stereo'):
            (stereo_file_paths, timestamps) = self._dataset.stereo_sequences_by_timestamp(
                time_range=self.time_range, preprocessed=self.load_preprocessed)
            self._image_loader = ImageLoader(stereo_file_paths, self.downsampling)
            self._timestamps = list(timestamps)
        else:
            raise NotImplementedError('Non-chunked loading of non-stereo image sequences is not implemented!')

    def get_times(self):
        return iter(self._timestamps)

    def get_image_shape(self):
        return self._image_shape

    # From DataLoader

    def load(self):
        print(self.__class__.__name__ + ': Loading...')
        self._image_shape = self._dataset.get_image_shape(
            self.sequences[0], self.downsampling)
        self._image_loader.load()

    def stop_loading(self):
        self._image_loader.stop_loading()

    # From DataGenerator

    def reset(self):
        self._image_loader.reset()

    def next(self):
        """Performs stereo reconstruction on the next images to reconstruct.
        If there are no images left to reconstruct, raises StopIteration."""
        images = next(self._image_loader)
        return images

    def __len__(self):
        return len(self._image_loader)

    # From ArraySource

    def get_array_ctype(self):
        return ctypes.c_double

    def get_array_shape(self):
        return (np.prod(self.get_image_shape()), 3)

