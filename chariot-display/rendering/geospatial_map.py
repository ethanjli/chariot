"""Classes for rendering geospatial maps."""
import matplotlib.pyplot as plt
import cartopy

class MapCanvas(object):
    def __init__(self):
        self.ax = plt.axes(projection=cartopy.crs.Mercator())
        self.ax.set_extent((-122.18383, -122.15447, 37.42149, 37.43545))

    def start_rendering(self):
        plt.show()

    def populate_map(self, dataset):
        self.ax.add_feature(dataset.get_feature('roads'), edgecolor='black', facecolor='')
        self.ax.add_feature(dataset.get_feature('buildings'),
                            edgecolor='gray', facecolor='gray')
        self.ax.add_feature(dataset.get_feature('landuse'),
                            edgecolor='gray', facecolor='gray')
        self.ax.add_feature(dataset.get_feature('natural'), edgecolor='green', facecolor='')
