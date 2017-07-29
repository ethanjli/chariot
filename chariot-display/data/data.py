import threading
try:
        from Queue import Queue, Empty, Full
except ImportError:
        from queue import Queue, Empty, Full

import ctypes

import h5py

from utilities import util

class DataGenerator(object):
    """Abstract base interface for various data generators."""
    def __init__(self, *args, **kwargs):
        super(DataGenerator, self).__init__(*args, **kwargs)

    def reset(self):
        """Resets the data generator.
        The next data to generate should be the first data."""
        pass

    def __next__(self):
        return self.next()

    def next(self):
        """Generates the next data.
        Raises a StopIteration when there is no next data to generate."""
        pass

    def __len__(self):
        """Returns the length of the generated sequence of data.
        Returns None if unknown."""
        return None

class DataLoader(object):
    """Abstract base interface for various data loaders."""
    def __init__(self, *args, **kwargs):
        super(DataGenerator, self).__init__(*args, **kwargs)

    def load(self):
        """Loads (or begins loading) all data."""
        pass

    def stop_loading(self):
        """Stops loading all data, if necessary."""
        pass

class ArraySource(object):
    """Abstract base interface for things which output constant-shape arrays."""

    @property
    def array_ctype(self):
        """Returns the ctype of the data stored in the array.
        Returns None if unknown."""
        return None

    @property
    def array_shape(self):
        """Returns the shape of each array.
        Returns None if unknown."""
        return None

class ArraysSource(object):
    """Abstract base interface for things which output constant-shape arrays of different shapes."""

    @property
    def array_ctypes(self):
        """Returns the ctypes of the data stored in the arrays in a fixed order.
        Returns None if unknown."""
        return None

    @property
    def array_shapes(self):
        """Returns the shapes of each array in a fixed order.
        Returns None if unknown."""
        return None


# CONCURRENT I/O

class ConcurrentDataLoader(DataLoader, DataGenerator):
    """Mix-in for loading data in a separate thread.
    For proper multiple inheritance MRO, this should be the leftmost base class.

    Method _load_next(self) needs to be implemented somewhere. It should return
    the next data, or None if the next data does not exist. If it returns an
    empty tuple instead of None, next() will never return None.
    """
    def __init__(self, max_size, discard_upon_none=True, *args, **kwargs):
        super(ConcurrentDataLoader, self).__init__(*args, **kwargs)
        self.__loader_thread = None
        self._data_queue = Queue(max_size)
        self._load = True
        self._discard_upon_none = discard_upon_none

    def _on_load(self):
        """Called every time the data loader is about to add data."""
        pass

    def _load_sync(self, block=True, timeout=1):
        """The thread function which continuously loads new data into memory."""
        print(self.__class__.__name__ + ': Loading...')
        while self._load:
            self._on_load()
            next_data = self._load_next()
            while self._load:
                try:
                    self._data_queue.put(next_data, block, timeout)
                    break
                except Full:
                    pass

            if next_data is None and self._discard_upon_none:
                self._load = False

    # From DataLoader

    def load(self):
        """Makes a new thread which concurrently loads new data into memory."""
        super(ConcurrentDataLoader, self).load()
        if self.__loader_thread is not None:
            print(self.__class__.__name__ + ' Warning: Already loading. Doing nothing.')
            return
        self.__loader_thread = threading.Thread(target=self._load_sync,
                                                name=self.__class__.__name__)
        self.__loader_thread.start()

    def stop_loading(self):
        """Stops the thread which is concurrently loading new data into memory."""
        self._load = False
        if self.__loader_thread is None:
            print(self.__class__.__name__ + ' Warning: Not currently loading data. Doing nothing.')
            return
        self.__loader_thread.join()
        self.__loader_thread = None
        super(ConcurrentDataLoader, self).stop_loading()

    # From DataGenerator

    def reset(self):
        """Stops the thread which is concurrently loading new data.
        After this is called, we can call load again."""
        if self.__loader_thread is not None:
            self.stop_loading()
        super(ConcurrentDataLoader, self).reset()
        self._load = True

    def next(self, block=True, timeout=None):
        """Gets the next loaded data and returns it.
        If no data is loaded, raises StopIteration."""
        if not self._load:
            raise StopIteration
        next_data = self._data_queue.get(block, timeout)
        if next_data is None:
            raise StopIteration
        return next_data

class PreloadingConcurrentDataLoader(ConcurrentDataLoader):
    """Blocks in the parent thread until the data buffer in memory is initially filled.
    For proper multiple inheritance MRO, this should be the leftmost base class.
    """

    # From ConcurrentDataLoader

    def _on_load(self):
        if self._data_queue.full():
            self._queue_filled.set()

    # From DataLoader

    def load(self, loading_wait_interval=1):
        """Start the loading, and wait until the queue is filled for the first time.
        If loading_wait_interval is 0, don't wait (behave like a plain old DataLoader).
        """
        self._queue_filled = threading.Event()
        print(self.__class__.__name__ + ': Waiting for enough data to be loaded...')
        super(PreloadingConcurrentDataLoader, self).load()
        if loading_wait_interval == 0:
            return
        try:
            while self._load and not self._queue_filled.wait(loading_wait_interval):
                pass
            self._load = True
        except KeyboardInterrupt:
            self._load = False
            print(self.__class__.__name__ + ': Exiting early...')
            raise KeyboardInterrupt

    # From DataGenerator

    def reset(self):
        self._queue_filled.clear()
        super(PreloadingConcurrentDataLoader, self).reset()

# CHUNKED DATA

def load_chunk_array(chunk):
    loaded = chunk[()]
    return loaded

class DataChunkLoader(DataLoader, DataGenerator, ArraySource):
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

    @property
    def array_ctype(self):
        return ctypes.c_ubyte

    @property
    def array_shape(self, cache={}):
        if self.archive_path not in cache:
            with h5py.File(self.archive_path, 'r') as hf:
                cache[self.archive_path] = hf['chunks']['0'].shape
        return cache[self.archive_path]

class PreloadingDataChunkLoader(DataChunkLoader):
    def __init__(self, *args, **kwargs):
        super(PreloadingDataChunkLoader, self).__init__(*args, **kwargs)
        self._all_loaded_chunks = None
        self._loaded_chunks = None

    # From DataLoader

    def load(self):
        if self._hf is not None:
            print(self.__class__.__name__ + ' Warning: Already loaded. Doing nothing.')
            return
        super(PreloadingDataChunkLoader, self).load()
        num_chunks = len(self._all_chunks)
        self._all_loaded_chunks = [self._load_next() for _ in range(num_chunks)]
        self._loaded_chunks = iter(self._all_loaded_chunks)

    # From DataGenerator

    def reset(self):
        if self._all_loaded_chunks is None:
            print(self.__class__.__name__ + ' Warning: Nothing to reset. Doing nothing.')
            return # Nothing to reset
        self._loaded_chunks = iter(self._all_loaded_chunks)

    def next(self):
        if self._all_loaded_chunks is None:
            raise RuntimeError(self.__class__.__name__ + ' Error: You need to call the load method first!')
        return next(self._loaded_chunks)

class ConcurrentDataChunkLoader(ConcurrentDataLoader, DataChunkLoader):
    """Loads chunks of data stored in an hdf5 chunk archive in a separate thread."""
    def __init__(self, archive_path, max_size=2, *args, **kwargs):
        super(ConcurrentDataChunkLoader, self).__init__(
            max_size, discard_upon_none=False, archive_path=archive_path, *args, **kwargs)

class PreloadingConcurrentDataChunkLoader(PreloadingConcurrentDataLoader, DataChunkLoader):
    """Blocks in the parent thread until the chunks buffer in the RAM is initially filled."""
    def __init__(self, archive_path, max_size=2, *args, **kwargs):
        super(PreloadingConcurrentDataChunkLoader, self).__init__(
            max_size, discard_upon_none=False, archive_path=archive_path, *args, **kwargs)

class SynchronizedDataChunkLoaders(DataLoader, DataGenerator, ArraySource):
    """Loads chunks of data split across multiple hdf5 chunk archives.
    Archives should have the chunks and chunk contents indexed identically.
    """
    def __init__(self, archive_paths, lazy=False, ChunkLoader=DataChunkLoader,
                 *args, **kwargs):
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
