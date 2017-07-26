"""Classes for rendering point clouds."""
import numpy as np
import vispy.visuals
import vispy.gloo

from utilities import util, profiling
import visuals

VERTEX_SHADER_FILENAME = 'point_cloud.vert'
FRAGMENT_SHADER_FILENAME = 'point_cloud.frag'

class Visual(visuals.ShadedVisual):
    def __init__(self):
        super(Visual, self).__init__(VERTEX_SHADER_FILENAME, FRAGMENT_SHADER_FILENAME)
        self._initialize_rendering()
        self.framerate_counter = profiling.FramerateCounter()

    def initialize_data(self, num_points):
        self.num_points = num_points
        self.data = np.zeros(num_points, [('a_position', np.float32, 3),
                                          ('a_color', np.float32, 3)])
        self.data_vbo = vispy.gloo.VertexBuffer(self.data)
        self.program.bind(self.data_vbo)
        self.updated_state = False

    def update_data(self, point_cloud):
        self.update_list_data(point_cloud.points, point_cloud.colors)

    def update_grid_data(self, points, rgb):
        """Updates the point cloud data, given by one point per grid cell, and re-renders it."""
        self.update_list_data(util.grid_data_to_list_data(points),
                              util.grid_data_to_list_data(rgb))

    def update_list_data(self, points, rgb):
        """Updates the point cloud data, given by one point per row, and re-renders it.
        Data are all assumed to be of the same number of points.
        """
        prev_num_points = self.num_points
        util.update_list_data_buffer(self.data['a_position'], points, prev_num_points)
        util.update_list_data_buffer(self.data['a_color'], rgb, prev_num_points)
        self.num_points = points.shape[0]
        self.updated_state = True
        self.data_vbo.set_data(self.data)
        self.framerate_counter.tick()

    def redraw(self):
        if self.updated_state:
            self.program.bind(self.data_vbo)
        super(Visual, self).redraw()

    def _initialize_rendering(self):
        u_linewidth = 1.0
        u_antialias = 1.0
        self.set_param('u_linewidth', u_linewidth)
        self.set_param('u_antialias', u_antialias)

    def draw(self, transforms):
        # Note we use the "additive" GL blending settings so that we do not
        # have to sort the mesh triangles back-to-front before each draw.
        # gloo.set_state('additive', cull_face=False)

        self.bind_transforms(transforms)
        # Finally, draw the triangles.
        self.program.draw('points')

    def update_scale(self, pixel_scale):
        self.set_param('u_size', 2 * pixel_scale)

class LocalVisual(Visual):
    def __init__(self):
        super(LocalVisual, self).__init__()

    @staticmethod
    def base_transform():
        transform = vispy.visuals.transforms.AffineTransform()
        transform.rotate(-90.0, (1, 0, 0))
        transform.translate((0, 1.5, 0))
        return transform

class GlobalVisual(Visual):
    def __init__(self):
        super(LocalVisual, self).__init__()

    @staticmethod
    def base_transform():
        transform = vispy.visuals.transforms.AffineTransform()
        return transform

