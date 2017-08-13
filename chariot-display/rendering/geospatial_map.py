"""Classes for rendering geospatial maps."""
import os
import math

import matplotlib.pyplot as plt
import matplotlib.animation as ma
import cartopy

from utilities import files
from data import gps_tracks
from datasets import datasets

class MapCanvas(object):
    def __init__(self, **kwargs):
        self.fig = plt.figure(**kwargs)
        self.ax = self.fig.add_subplot(111, projection=cartopy.crs.Mercator())
        self.ax.set_position([0, 0, 1, 1])
        self._location_indicator_size = None

    def hide_borders(self):
        self.fig.patch.set_visible(False)
        self.ax.patch.set_visible(False)
        self.ax.background_patch.set_visible(False)
        self.ax.outline_patch.set_visible(False)

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
        self._draw_location_indicator(*track.coordinates_and_deltas[0])

    def _draw_location_indicator(self, x, y, dx, dy):
        length = math.sqrt(dx * dx + dy * dy)
        size = self._location_indicator_size
        self.indicator = self.ax.arrow(x, y, dx * size / length, dy * size / length,
                                       transform=cartopy.crs.PlateCarree(),
                                       length_includes_head=True, width=0,
                                       head_length=size, head_width=size, overhang=-0.2,
                                       linewidth=0)
        return self.indicator

    def update_location_indicator(self, x, y, dx, dy):
        self.indicator.remove()
        return self._draw_location_indicator(x, y, dx, dy)

    def focus_location_indicator(self, x, y, longitude_margins=0.0025,
                                 latitude_margins=0.002):
        bounds = (x - longitude_margins, x + longitude_margins,
                  y - latitude_margins, y + latitude_margins)
        self.ax.set_extent(bounds)

    def register_animator(self, animator, **kwargs):
        self.animation = ma.FuncAnimation(
            self.fig, animator.execute, animator.frames, **kwargs
        )

class TrackAnimator(object):
    """Abstract base class for animating a track on a MapCanvas."""
    def __init__(self, track_name, datasets_path=datasets.DATASETS_PATH):
        self.track = gps_tracks.KMLSequence(os.path.join(datasets.DATASETS_PATH, track_name))
        self._datasets_path = datasets_path
        self.track.load()

    @property
    def frames(self):
        return self.track.coordinates_and_deltas

    def start_rendering_to_file(self, name, format='png', **kwargs):
        output_path = os.path.join(self._datasets_path, name)
        files.make_dir_path(output_path)
        screenshot_counter = 0
        for frame in self.frames:
            self.execute(frame)
            file_path = os.path.join(output_path, str(screenshot_counter) + '.' + format)
            self.on_save(frame, file_path)
            screenshot_counter += 1

    def on_save(self, frame_input, save_path, **kwargs):
        """Do any necessary work after to save the current frame."""
        plt.savefig(save_path, **kwargs)

