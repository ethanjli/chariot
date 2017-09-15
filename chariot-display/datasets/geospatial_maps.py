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
        self._bounds = None

    def get_path(self, shape_name):
        return os.path.join(self.parent_path, self.name, 'shape', shape_name + '.shp')

    def get_feature(self, shape_name):
        reader = cartopy.io.shapereader.Reader(self.get_path(shape_name))
        feature = cartopy.feature.ShapelyFeature(reader.geometries(),
                                                 cartopy.crs.PlateCarree())
        return feature

    @property
    def bounds(self):
        if self._bounds is None:
            self._bounds = self.parse_bounds()
        return self._bounds

    def parse_bounds(self):
        readme_path = os.path.join(self.parent_path, self.name, 'README.txt')
        with open(readme_path, 'r') as f:
            for line in f:
                if line.startswith('GPS rectangle coordinates (lng,lat)'):
                    coordinates = line.split(': ')[1]
                    break
        (minima, maxima) = coordinates.split(' x ')
        (min_long, min_lat) = minima.split(',')
        (max_long, max_lat) = maxima.split(',')
        return tuple(float(bound) for bound in [min_long, max_long, min_lat, max_lat])

    # From datasets.Dataset

    @property
    def parent_path(self):
        """Returns the path of the parent of the dataset."""
        if self._parent_path:
            return self._parent_path
        else:
            return datasets.DATASETS_PATH

