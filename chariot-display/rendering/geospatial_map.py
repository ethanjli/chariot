"""Classes for rendering geospatial maps."""
import matplotlib.pyplot as plt
import cartopy

class MapCanvas(object):
    def __init__(self):
        self.ax = plt.axes(projection=cartopy.crs.Mercator())
        #self.ax.stock_img()
        #self.ax.coastlines()
        self.ax.set_extent((-122.18383, -122.15447, 37.42149, 37.43545))

    def start_rendering(self):
        plt.show()

    def add_roads(self, roads_feature):
        self.ax.add_feature(roads_feature, edgecolor='black', facecolor='')
