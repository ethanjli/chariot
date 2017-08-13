from data import gps_tracks
from datasets import geospatial_maps
from rendering import geospatial_map
from tests.unit._data.gps_tracks import TRACK_KML_PATH

dataset = geospatial_maps.Dataset('planet-osm_Stanford_Campus')
track = gps_tracks.KMLSequence(TRACK_KML_PATH)
track.load()
map_canvas = geospatial_map.MapCanvas()
map_canvas.initialize_map(dataset)
map_canvas.initialize_track(track)
map_canvas.initialize_location_indicator(track)
map_canvas.update_location_indicator(*track.coordinates_and_deltas[30])
map_canvas.start_rendering()
