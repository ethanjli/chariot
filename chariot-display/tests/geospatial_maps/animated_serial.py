import os

from data import gps_tracks
from datasets import datasets, geospatial_maps
from rendering import geospatial_map

class Animator(object):
    def __init__(self):
        self.dataset = geospatial_maps.Dataset('planet-osm_Stanford_Campus')
        self.track = gps_tracks.KMLSequence(
            os.path.join(datasets.DATASETS_PATH, 'mytracks_20170804_125713.kml')
        )
        self.track.load()

    def register_canvas(self, canvas):
        self.canvas = canvas
        canvas.initialize_map(self.dataset)
        canvas.initialize_track(self.track)
        canvas.initialize_location_indicator(self.track)
        canvas.register_animator(self)

    def execute(self, frame_input):
        return (self.canvas.update_location_indicator(*frame_input),)

    @property
    def frames(self):
        return self.track.coordinates_and_deltas


def main():
    canvas = geospatial_map.MapCanvas()
    animator = Animator()
    animator.register_canvas(canvas)
    canvas.start_rendering()


if __name__ == '__main__':
    main()


