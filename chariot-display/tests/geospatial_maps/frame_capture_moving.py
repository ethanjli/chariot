import os
import time
import math

import svgutils
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

from utilities import figures
from datasets import geospatial_maps
from rendering import geospatial_map

OUTPUT_NAME = 'Chariot_Map_' + time.strftime('%Y%m%d')
OUTPUT_DPI = 120

class Animator(geospatial_map.TrackAnimator):
    def __init__(self):
        super(Animator, self).__init__('mytracks_20170804_125713.kml')
        self.dataset = geospatial_maps.Dataset('planet-osm_Stanford_Campus')

    def register_canvas(self, canvas):
        self.canvas = canvas
        self.canvas.hide_borders()
        canvas.initialize_map(self.dataset)
        canvas.initialize_track(self.track.track)
        canvas.initialize_location_indicator(self.track.track)
        canvas.register_animator(self)

    def execute(self, frame_input):
        location_indicator = self.canvas.update_location_indicator(*frame_input)
        self.canvas.focus_location_indicator(frame_input[0], frame_input[1])
        return (location_indicator,)

    def on_save(self, frame_input, save_path, save_dpi=72, **kwargs):
        svg = figures.to_svg(self.canvas.fig, **kwargs)
        width = int(svg.get_size()[0])
        height = int(svg.get_size()[1])
        output = svgutils.compose.Figure(width, height, svg.getroot())
        self.scale_to_rotation_safe_viewport(output, width, height)
        self.rotate_to_location_indicator(output, frame_input, width / 2, height / 2)
        self.export_png(output, save_path, save_dpi)

    def scale(self, figure, scale_factor, center_x, center_y):
        figure.move(-center_x, -center_y)
        figure.scale(scale_factor)
        figure.move(center_x, center_y)

    def scale_to_rotation_safe_viewport(self, figure, width, height):
        scale_factor = math.sqrt(width ** 2 + height ** 2) / min(width, height)
        self.scale(figure, scale_factor, width / 2, height / 2)

    def rotate_to_location_indicator(self, figure, frame_input, indicator_x, indicator_y):
        (dx, dy) = frame_input[2:]
        rotation = -90 + math.degrees(math.atan2(dy, dx))
        figure.rotate(rotation, indicator_x, indicator_y)

    def export_png(self, figure, save_path, dpi):
        figure.save(save_path)
        drawing = svg2rlg(save_path)
        drawing.scale(1.0 * dpi / 72, 1.0 * dpi / 72)
        renderPM.drawToFile(drawing, os.path.splitext(save_path)[0] + '.png', dpi=dpi)
        os.remove(save_path)


def main():
    canvas = geospatial_map.MapCanvas(
        frameon=False, figsize=(5, 5 * math.sqrt(3)),
        dpi=72  # Figure DPI of 72 assumed by svgutils
    )
    animator = Animator()
    animator.register_canvas(canvas)
    animator.start_rendering_to_file(OUTPUT_NAME, format='svg', save_dpi=OUTPUT_DPI, transparent=True)


if __name__ == '__main__':
    main()

