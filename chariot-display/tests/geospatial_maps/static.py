from datasets import geospatial_maps
from rendering import geospatial_map

dataset = geospatial_maps.Dataset('planet-osm_Stanford_Campus')
#dataset = geospatial_maps.Dataset('planet-osm_Hella_Ventures')
map_canvas = geospatial_map.MapCanvas()
map_canvas.populate_map(dataset)
map_canvas.start_rendering()
