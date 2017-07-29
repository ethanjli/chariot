"""Interfaces for loading and generation of data."""

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

