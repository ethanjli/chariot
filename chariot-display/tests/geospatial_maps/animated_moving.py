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
        canvas.initialize_location_indicator(self.track)
        canvas.register_animator(self)

    def execute(self, frame_input):
        location_indicator = self.canvas.update_location_indicator(*frame_input)
        self.canvas.focus_location_indicator(frame_input[0], frame_input[1])
        return (location_indicator,)


def main():
    canvas = geospatial_map.MapCanvas()
    animator = Animator()
    animator.register_canvas(canvas)
    canvas.start_rendering()


if __name__ == '__main__':
    main()


