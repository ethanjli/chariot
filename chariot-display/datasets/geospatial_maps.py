"""Functions and classes for loading of geospatial map data."""
import os

import cartopy

import datasets

SHAPES = [
    'buildings', 'landuse', 'natural', 'places', 'points', 'railways', 'roads', 'waterways'
]

class Dataset(datasets.Dataset):
    """A collection of shapefiles for a region."""
    def __init__(self, name, parent_path=None):
        self.name = name
        self._parent_path = parent_path

    def get_path(self, shape_name):
        return os.path.join(self.parent_path, self.name, 'shape', shape_name + '.shp')

    def get_feature(self, shape_name):
        reader = cartopy.io.shapereader.Reader(self.get_path(shape_name))
        feature = cartopy.feature.ShapelyFeature(reader.geometries(),
                                                 cartopy.crs.PlateCarree())
        return feature

    # From datasets.Dataset

    @property
    def parent_path(self):
        """Returns the path of the parent of the dataset."""
        if self._parent_path:
            return self._parent_path
        else:
            return datasets.DATASETS_PATH

