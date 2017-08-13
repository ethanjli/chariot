"""Classes for rendering geospatial maps."""
import math

import matplotlib.pyplot as plt
import cartopy

class MapCanvas(object):
    def __init__(self):
        self.ax = plt.axes(projection=cartopy.crs.Mercator())

    def start_rendering(self):
        plt.show()

    def populate_map(self, dataset):
        self.ax.add_feature(dataset.get_feature('roads'), edgecolor='black', facecolor='')
        self.ax.add_feature(dataset.get_feature('buildings'),
                            edgecolor='gray', facecolor='gray')
        self.ax.add_feature(dataset.get_feature('landuse'),
                            edgecolor='gray', facecolor='gray')
        self.ax.add_feature(dataset.get_feature('natural'), edgecolor='green', facecolor='')
        self.ax.set_extent(dataset.bounds)

    def plot_track(self, track, longitude_margins=0.001, latitude_margins=0.001):
        plt.plot(track.longitudes, track.latitudes, transform=cartopy.crs.PlateCarree(),
                 color='blue')
        bounds = list(track.bounds)
        bounds[0] -= longitude_margins
        bounds[1] += longitude_margins
        bounds[2] -= latitude_margins
        bounds[3] += latitude_margins
        self.ax.set_extent(bounds)

    def plot_location_indicator(self, x, y, dx, dy, size=0.00025):
        length = math.sqrt(dx * dx + dy * dy)
        self.indicator = self.ax.arrow(x, y, dx * size / length, dy * size / length,
                                       transform=cartopy.crs.PlateCarree(),
                                       length_includes_head=True, width=0,
                                       head_length=size, head_width=size, overhang=-0.2,
                                       linewidth=0)

