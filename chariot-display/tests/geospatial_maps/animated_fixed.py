from datasets import geospatial_maps
from rendering import geospatial_map

class Animator(geospatial_map.TrackAnimator):
    def __init__(self):
        super(Animator, self).__init__('mytracks_20170804_125713.kml')
        self.dataset = geospatial_maps.Dataset('planet-osm_Stanford_Campus')

    def register_canvas(self, canvas):
        self.canvas = canvas
        canvas.initialize_map(self.dataset)
        canvas.initialize_track(self.track)
        canvas.initialize_location_indicator(self.track, size=24.0)
        canvas.register_animator(self, blit=True)

    def execute(self, frame_input):
        return (self.canvas.update_location_indicator(*frame_input),)


def main():
    canvas = geospatial_map.MapCanvas(figsize=(5, 5), dpi=60)
    animator = Animator()
    animator.register_canvas(canvas)
    canvas.start_rendering()


if __name__ == '__main__':
    main()


