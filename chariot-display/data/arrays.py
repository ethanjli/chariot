"""Interfaces for loading arrays, supporting parallel processing."""
import multiprocessing
import operator

import numpy as np

from utilities import parallelism

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
    """Abstract base interface for things which output multiple arrays.
    Each array may be of a different shape.
    """

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

# PARALLEL LOADING

class SynchronizedBuffer(object):
    def __init__(self):
        self.__shared_base = None
        self.array = None

    def initialize(self, ctype, shape):
        num_elements = reduce(operator.mul, shape, 1)
        self.__shared_base = multiprocessing.Array(ctype, num_elements)
        self.buffer = np.ctypeslib.as_array(self.__shared_base.get_obj()).reshape(*shape)

class DoubleBuffer(parallelism.DoubleBuffer):
    def __init__(self):
        super(DoubleBuffer, self).__init__()
        self._arrays = [SynchronizedBuffer(), SynchronizedBuffer()]

    def initialize(self, ctype, shape):
        for array in self._arrays:
            array.initialize(ctype, shape)

    def get_buffer(self, buffer_id):
        return self._arrays[buffer_id].buffer

class ParallelLoader(parallelism.LoaderGeneratorProcess, ArraySource):
    """Loads numpy arrays sequentially in a separate process into shared memory.
    ArraySourceLoaderGeneratorFactory should return an object which is a Loader,
    a Generator, and also an ArraySource. This object should generate an array of
    constant shape.
    """
    def __init__(self, ArraySourceLoaderGeneratorFactory, *args, **kwargs):
        super(ParallelLoader, self).__init__(
            ArraySourceLoaderGeneratorFactory, DoubleBuffer, *args, **kwargs)
        self.double_buffer.initialize(self.loader.array_ctype(),
                                      self.loader.array_shape())

    # From DoubleBufferedProcess

    def on_write_to_buffer(self, data, write_buffer):
        np.copyto(write_buffer, data)

    # From LoaderGeneratorProcess

    def unmarshal_output(self, marshalled, read_buffer):
        return read_buffer

    # From ArraySource

    @property
    def array_ctype(self):
        return self._loader.get_array_ctype()

    @property
    def array_shape(self):
        return self._loader.get_array_shape()

