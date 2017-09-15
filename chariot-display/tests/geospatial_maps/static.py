import os

from data import gps_tracks
from datasets import datasets, geospatial_maps
from rendering import geospatial_map

dataset = geospatial_maps.Dataset('planet-osm_Stanford_Campus')
track = gps_tracks.KMLSequence(
    os.path.join(datasets.DATASETS_PATH, 'mytracks_20170804_125713.kml')
)
track.load()
map_canvas = geospatial_map.MapCanvas(figsize=(5, 5), dpi=60)
map_canvas.initialize_map(dataset)
map_canvas.initialize_track(track.track)
map_canvas.initialize_location_indicator(track.track, size=24.0)
map_canvas.update_location_indicator(*track.track.coordinates_and_deltas[30])
map_canvas.start_rendering()
