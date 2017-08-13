"""Classes for rendering geospatial maps."""
import math

import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy

class MapCanvas(object):
    def __init__(self):
        self.fig = plt.figure()
        self.ax = plt.axes(projection=cartopy.crs.Mercator())
        self._location_indicator_size = None

    def start_rendering(self):
        plt.show()

    def initialize_map(self, dataset):
        self.ax.add_feature(dataset.get_feature('roads'), edgecolor='black', facecolor='')
        self.ax.add_feature(dataset.get_feature('buildings'),
                            edgecolor='gray', facecolor='gray')
        self.ax.add_feature(dataset.get_feature('landuse'),
                            edgecolor='gray', facecolor='gray')
        self.ax.add_feature(dataset.get_feature('natural'), edgecolor='green', facecolor='')
        self.ax.set_extent(dataset.bounds)

    def initialize_track(self, track, longitude_margins=0.001, latitude_margins=0.001):
        plt.plot(track.longitudes, track.latitudes, transform=cartopy.crs.PlateCarree(),
                 color='blue')
        bounds = list(track.bounds)
        bounds[0] -= longitude_margins
        bounds[1] += longitude_margins
        bounds[2] -= latitude_margins
        bounds[3] += latitude_margins
        self.ax.set_extent(bounds)

    def initialize_location_indicator(self, track, size=0.0002):
        self._location_indicator_size = size
        self.indicator = self._draw_location_indicator(*track.coordinates_and_deltas[0])

    def _draw_location_indicator(self, x, y, dx, dy):
        length = math.sqrt(dx * dx + dy * dy)
        size = self._location_indicator_size
        return self.ax.arrow(x, y, dx * size / length, dy * size / length,
                             transform=cartopy.crs.PlateCarree(),
                             length_includes_head=True, width=0,
                             head_length=size, head_width=size, overhang=-0.2,
                             linewidth=0)

    def update_location_indicator(self, x, y, dx, dy):
        self.indicator.remove()
        self._draw_location_indicator(x, y, dx, dy)

