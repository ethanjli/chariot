"""Classes for loading data concurrently in separate threads."""
import threading
try:
        from Queue import Queue, Full
except ImportError:
        from queue import Queue, Full

from utilities import concurrency
import data

class Loader(data.DataLoader, data.DataGenerator, concurrency.Thread):
    """Mix-in for loading data in a separate thread.
    For proper multiple inheritance MRO, this should be the leftmost base class.

    Method load_next(self) needs to be implemented somewhere. It should return
    the next data, or None if the next data does not exist. If it returns an
    empty tuple instead of None, next() will never return None.
    """
    def __init__(self, max_size, discard_upon_none, *args, **kwargs):
        super(Loader, self).__init__(*args, **kwargs)
        self.__loader_thread = None
        self._data_queue = Queue(max_size)
        self._run = True
        self._load = False
        self._discard_upon_none = discard_upon_none

    def _on_load(self):
        """Called every time the data loader is about to add data.
        Implement this."""
        pass

    def _enqueue(self, next_data, block=True, timeout=1):
        while self._run and self._load:
            try:
                self._data_queue.put(next_data, block, timeout)
                break
            except Full:
                pass

    # From Thread

    def on_run_start(self):
        print(self.__class__.__name__ + ': Loading...')

    def execute(self, block=True, timeout=1):
        if not self._load:
            return
        self._on_load()
        next_data = self.load_next()
        self._enqueue(next_data, block, timeout)
        if next_data is None:
            self._load = False
            if self._discard_upon_none:
                self._run = False

    # From DataLoader

    def load(self):
        """Makes a new thread which concurrently loads new data into memory."""
        super(Loader, self).load()
        self._load = True
        self.run_concurrent()

    def stop_loading(self):
        """Stops the thread which is concurrently loading new data into memory."""
        self._load = False
        self.terminate()
        super(Loader, self).stop_loading()

    # From DataGenerator

    def reset(self):
        """Stops the thread which is concurrently loading new data.
        After this is called, we can call load again."""
        if self.__loader_thread is not None:
            self.stop_loading()
        super(Loader, self).reset()
        self._run = True
        self._load = True

    def next(self, block=True, timeout=None):
        """Gets the next loaded data and returns it.
        If no data is loaded, raises StopIteration."""
        if not self._run:
            raise StopIteration
        next_data = self._data_queue.get(block, timeout)
        if next_data is None:
            raise StopIteration
        return next_data

class PreloadingLoader(Loader):
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
        If loading_wait_interval is 0, don't wait (behave like a plain old Loader).
        """
        self._queue_filled = threading.Event()
        print(self.__class__.__name__ + ': Waiting for enough data to be loaded...')
        super(Loader, self).load()
        if loading_wait_interval == 0:
            return
        try:
            while self._run and not self._queue_filled.wait(loading_wait_interval):
                pass
            self._run = True
        except KeyboardInterrupt:
            self._run = False
            print(self.__class__.__name__ + ': Exiting early...')
            raise KeyboardInterrupt

    # From DataGenerator

    def reset(self):
        self._queue_filled.clear()
        super(Loader, self).reset()

