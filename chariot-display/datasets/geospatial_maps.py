"""Functions and classes for loading of geospatial map data."""
import os

import cartopy

import datasets

class Dataset(datasets.Dataset):
    """A collection of shapefiles for a region."""
    def __init__(self, name, parent_path=None):
        self.name = name
        self._parent_path = parent_path

    @property
    def roads_path(self):
        return os.path.join(self.parent_path, self.name, 'shape', 'roads.shp')

    @property
    def roads_feature(self):
        reader = cartopy.io.shapereader.Reader(self.roads_path)
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

