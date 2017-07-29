"""Interfaces for loading arrays, supporting parallel processing."""

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

