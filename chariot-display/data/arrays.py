"""Interfaces for loading arrays, supporting parallel processing."""
import parallelism
import multiprocessing
import operator

import numpy as np
from numpy.ctypeslib import as_array

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

# PARALLEL LOADING

class DoubleBuffer(parallelism.DoubleBuffer):
    def __init__(self):
        super(DoubleBuffer, self).__init__()
        self._array_bases = [None, None]
        self._arrays = [None, None]

    def initialize(self, ctype, shape):
        num_elements = reduce(operator.mul, shape, 1)

        self._array_bases[0] = multiprocessing.Array(ctype, num_elements)
        self._array_bases[1] = multiprocessing.Array(ctype, num_elements)

        self._arrays[0] = np.ctypeslib.as_array(
            self._array_bases[0].get_obj()).reshape(*shape)
        self._arrays[1] = as_array(
            self._array_bases[1].get_obj()).reshape(*shape)

    def get_buffer(self, buffer_id):
        return self._arrays[buffer_id]

class ParallelLoader(parallelism.LoaderGeneratorProcess, ArraySource):
    """Loads numpy arrays sequentially in a separate process into shared memory."""
    def __init__(self, ArraySourceLoaderGeneratorFactory, *args, **kwargs):
        super(ParallelLoader, self).__init__(
            DoubleBuffer(), ArraySourceLoaderGeneratorFactory, *args, **kwargs)
        self._buffer.initialize(self.loader.array_ctype(),
                                self.loader.array_shape())

    # From LoaderGeneratorProcess

    def _on_load(self, loaded_next):
        np.copyto(self._buffer.write_buffer, loaded_next)
        return True

    def _process_result(self, result):
        return self._buffer.read_buffer

    # From ArraySource

    @property
    def array_ctype(self):
        return self._loader.get_array_ctype()

    @property
    def array_shape(self):
        return self._loader.get_array_shape()

