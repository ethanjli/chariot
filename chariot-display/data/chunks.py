"""Classes for loading chunked data from HDF5 chunk archives."""
import ctypes

import h5py

from utilities import util
import data
import asynchronous

def load_chunk_array(chunk):
    loaded = chunk[()]
    return loaded

class Loader(data.DataLoader, data.DataGenerator, data.ArraySource):
    """Loads chunks of data stored in an hdf5 chunk archive.

    Arguments:
        archive_path: the file path of the hdf5 chunk archive. The chunk archive should
        have a group named 'chunks' of zero-indexed chunks.
        lazy: whether to defer loading of chunk data from disk. If True, next() returns
        just the chunk; otherwise, next() returns both the chunk and the chunk data
        loaded from disk.
    """
    def __init__(self, archive_path, lazy=False):
        self.archive_path = archive_path
        self._hf = None
        self._all_chunks = None
        self._chunks = None
        self.lazy = lazy

    def __getitem__(self, chunk_id):
        return self._hf['chunks'][str(chunk_id)]

    def _load_next(self):
        try:
            next_chunk = self._hf['chunks'][next(self._chunks)]
        except StopIteration:
            return None
        if self.lazy:
            return next_chunk
        else:
            return (next_chunk, load_chunk_array(next_chunk))

    # From DataLoader

    def load(self):
        if self._hf is not None:
            print(self.__class__.__name__ + ' Warning: Already loading. Doing nothing.')
            return
        self._hf = h5py.File(self.archive_path, 'r')
        self._all_chunks = sorted(self._hf['chunks'].keys(), key=util.natural_keys)
        self._chunks = iter(self._all_chunks)

    def stop_loading(self):
        if self._hf is None:
            print(self.__class__.__name__ + ' Warning: Not currently loading. Doing nothing.')
            return
        self._hf.close()
        self._hf = None

    # From DataGenerator

    def reset(self):
        if self._hf is None:
            self.load()
        else:
            self._chunks = iter(self._all_chunks)

    def next(self):
        next_chunk = self._load_next()
        if next_chunk is None:
            raise StopIteration
        return next_chunk

    # From ArraySource

    def get_array_ctype(self):
        return ctypes.c_ubyte

    def get_array_shape(self, cache={}):
        if self.archive_path not in cache:
            with h5py.File(self.archive_path, 'r') as hf:
                cache[self.archive_path] = hf['chunks']['0'].shape
        return cache[self.archive_path]

class PreloadingLoader(Loader):
    def __init__(self, *args, **kwargs):
        super(PreloadingLoader, self).__init__(*args, **kwargs)
        self._all_loaded_chunks = None
        self._loaded_chunks = None

    # From DataLoader

    def load(self):
        if self._hf is not None:
            print(self.__class__.__name__ + ' Warning: Already loaded. Doing nothing.')
            return
        super(PreloadingLoader, self).load()
        num_chunks = len(self._all_chunks)
        self._all_loaded_chunks = [self._load_next() for _ in range(num_chunks)]
        self._loaded_chunks = iter(self._all_loaded_chunks)

    # From DataGenerator

    def reset(self):
        if self._all_loaded_chunks is None:
            print(self.__class__.__name__ + ' Warning: Nothing to reset. Doing nothing.')
            return  # Nothing to reset
        self._loaded_chunks = iter(self._all_loaded_chunks)

    def next(self):
        if self._all_loaded_chunks is None:
            raise RuntimeError(self.__class__.__name__ + ' Error: You need to call the load method first!')
        return next(self._loaded_chunks)

class AsynchronousLoader(asynchronous.Loader, Loader):
    """Loads chunks of data stored in an hdf5 chunk archive in a separate thread."""
    def __init__(self, archive_path, max_size=2, *args, **kwargs):
        super(AsynchronousLoader, self).__init__(
            max_size, discard_upon_none=False, archive_path=archive_path, *args, **kwargs)

class PreloadingAsynchronousLoader(asynchronous.PreloadingLoader, Loader):
    """Blocks in the parent thread until the chunks buffer in the RAM is initially filled."""
    def __init__(self, archive_path, max_size=2, *args, **kwargs):
        super(PreloadingAsynchronousLoader, self).__init__(
            max_size, discard_upon_none=False, archive_path=archive_path, *args, **kwargs)

class SynchronizedLoaders(data.DataLoader, data.DataGenerator, data.ArraySource):
    """Loads chunks of data split across multiple hdf5 chunk archives.
    Archives should have the chunks and chunk contents indexed identically.
    """
    def __init__(self, archive_paths, lazy=False, ChunkLoader=Loader, *args, **kwargs):
        if isinstance(archive_paths, str):
            archive_paths = [archive_paths]
        self.archive_paths = archive_paths
        self._chunk_loaders = [ChunkLoader(archive_path, *args, lazy=False, **kwargs)
                               for archive_path in archive_paths]
        self.lazy = self._chunk_loaders[0].lazy

    def __getitem__(self, chunk_id):
        return [chunk_loader[chunk_id]
                for chunk_loader in self._chunk_loaders]

    # From DataLoader

    def load(self):
        for chunk_loader in self._chunk_loaders:
            chunk_loader.load()

    def stop_loading(self):
        for chunk_loader in self._chunk_loaders:
            chunk_loader.stop_loading()

    # From DataGenerator

    def reset(self):
        for chunk_loader in self._chunk_loaders:
            chunk_loader.reset()

    def next(self):
        return [next(chunk_loader) for chunk_loader in self._chunk_loaders]

def save_chunk(path, chunk, chunk_index, chunk_attributes):
    hf = h5py.File(path, 'a')
    chunks = hf.require_group('chunks')
    chunk = chunks.create_dataset(str(chunk_index), data=chunk)
    for (name, value) in chunk_attributes.items():
        chunk.attrs[name] = value
    hf.close()
