from datasets import geospatial_maps
from rendering import geospatial_map

dataset = geospatial_maps.Dataset('planet-osm_Stanford_Campus')
map_canvas = geospatial_map.MapCanvas()
map_canvas.add_roads(dataset.roads_feature)
map_canvas.start_rendering()
