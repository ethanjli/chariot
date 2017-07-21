import numpy as np
import vispy.visuals
import vispy.io
import vispy.gloo

from utilities import util
from utilities import profiling
import visuals

MESH_VERTEX_SHADER_FILENAME = 'mesh.vert'
MESH_FRAGMENT_SHADER_FILENAME = 'mesh.frag'
POINT_CLOUD_MESH_VERTEX_SHADER_FILENAME = 'point_cloud_mesh.vert'
POINT_CLOUD_MESH_FRAGMENT_SHADER_FILENAME = 'point_cloud_mesh.frag'

class MeshVisual(visuals.ShadedVisual):
    def __init__(self, mesh_name=None, vertex_shader_filename=MESH_VERTEX_SHADER_FILENAME,
                 fragment_shader_filename=MESH_FRAGMENT_SHADER_FILENAME):
        super(MeshVisual, self).__init__(vertex_shader_filename, fragment_shader_filename)
        if mesh_name is not None:
            self.initialize_data(mesh_name)
        self.framerate_counter = profiling.FramerateCounter()

    def initialize_data(self, mesh_name=None, num_vertices=None, num_faces=None):
        if mesh_name is not None:
            (self.vertices, self.faces, self.normals, _) = visuals.load_model(mesh_name)
            self.num_vertices = self.vertices.shape[0]
            self.num_faces = self.faces.shape[0]
            self.faces_ibo = vispy.gloo.IndexBuffer(self.faces)
        else:
            self.num_vertices = num_vertices
            self.vertices = np.zeros((num_vertices, 3), dtype=np.float32)
            self.num_faces = num_faces
            self.normals = np.zeros((num_vertices, 3), dtype=np.float32)
            self.faces = np.zeros((num_faces, 3), dtype=np.uint32)
        self.vertices_vbo = vispy.gloo.VertexBuffer(self.vertices)
        self.program.vert['position'] = self.vertices_vbo
        self.normals_vbo = vispy.gloo.VertexBuffer(self.normals)
        self.program.vert['normal'] = self.normals_vbo

    def update_data(self, vertices, faces):
        prev_num_vertices = self.num_vertices
        util.update_list_data_buffer(self.vertices, vertices, prev_num_vertices)
        prev_num_faces = self.num_faces
        util.update_list_data_buffer(self.faces, faces, prev_num_faces)
        self.num_vertices = vertices.shape[0]
        self.num_faces = faces.shape[0]
        self.updated_state = True
        self.vertices_vbo.set_data(self.vertices)
        self.faces_ibo = vispy.gloo.IndexBuffer(self.faces)
        self.framerate_counter.tick()

    def redraw(self):
        if self.updated_state:
            super(MeshVisual, self).redraw()
            self.program.draw('triangles', self.faces_ibo)

    def draw(self, transforms):
        # Note we use the "additive" GL blending settings so that we do not
        # have to sort the mesh triangles back-to-front before each draw.
        # vispy.gloo.set_state('additive', cull_face=False)

        self.bind_transforms(transforms)
        # Finally, draw the triangles.
        self.program.draw('triangles', self.faces_ibo)

class PointCloudMeshVisual(visuals.ShadedVisual):
    def __init__(self):
        super(PointCloudMeshVisual, self).__init__(POINT_CLOUD_MESH_VERTEX_SHADER_FILENAME,
                                                   POINT_CLOUD_MESH_FRAGMENT_SHADER_FILENAME)
        self.framerate_counter = profiling.FramerateCounter()

    def initialize_data(self, num_vertices, num_faces):
        self.num_vertices = num_vertices
        self.vertices = np.zeros((num_vertices, 3), dtype=np.float32)
        self.vertices_vbo = vispy.gloo.VertexBuffer(self.vertices)
        self.program.vert['position'] = self.vertices_vbo
        self.colors = np.zeros((num_vertices, 3), dtype=np.float32)
        self.colors_vbo = vispy.gloo.VertexBuffer(self.colors)
        self.program.vert['color'] = self.colors_vbo

        self.num_faces = num_faces
        self.faces = np.zeros((num_faces, 3), dtype=np.uint32)
        self.faces_ibo = None

    def update_data(self, vertices, colors, faces):
        prev_num_vertices = self.num_vertices
        util.update_list_data_buffer(self.vertices, vertices, prev_num_vertices)
        util.update_list_data_buffer(self.colors, colors, prev_num_vertices)
        prev_num_faces = self.num_faces
        util.update_list_data_buffer(self.faces, faces, prev_num_faces)
        self.num_vertices = vertices.shape[0]
        self.num_faces = faces.shape[0]
        self.updated_state = True
        self.vertices_vbo.set_data(self.vertices)
        self.colors_vbo.set_data(self.colors)
        self.faces_ibo = vispy.gloo.IndexBuffer(self.faces)
        self.framerate_counter.tick()

    def redraw(self):
        if self.updated_state:
            super(PointCloudMeshVisual, self).redraw()
            if self.faces_ibo is None:
                print(self.__class__.__name__ + ' Warning: No faces to draw!')
                return
            self.program.draw('triangles', self.faces_ibo)

    def draw(self, transforms):
        # Note we use the "additive" GL blending settings so that we do not
        # have to sort the mesh triangles back-to-front before each draw.
        # vispy.gloo.set_state('additive', cull_face=False)

        self.bind_transforms(transforms)
        if self.faces_ibo is None:
            print(self.__class__.__name__ + ' Warning: No faces to draw!')
            return
        self.program.draw('triangles', self.faces_ibo)

class CarModelVisual(MeshVisual):
    def __init__(self, mesh_name='alfa147.obj'):
        super(CarModelVisual, self).__init__(mesh_name)
        self._initialize_rendering()

    def _initialize_rendering(self):
        self.set_param('u_ambientk', (0.5, 0.5, 0.5, 1.0))
        self.set_param('u_light_color', (1.0, 1.0, 1.0, 1.0))
        self.set_param('u_base_color', (0.0, 0.6, 0.8, 1.0))
        self.set_param('u_light_dir', (0.0, -1.0, 0.0))

    @staticmethod
    def base_transform():
        transform = vispy.visuals.transforms.AffineTransform()
        transform.rotate(-90, (1, 0, 0))
        transform.rotate(180, (0, 1, 0))
        transform.scale((0.025, 0.025, 0.025))
        return transform

    @staticmethod
    def apply_final_transform(transform):
        transform.translate((0, -0.5, 0.25))
        return transform

class StereoReconstructionMeshVisual(PointCloudMeshVisual):
    def __init__(self):
        super(StereoReconstructionMeshVisual, self).__init__()

    @staticmethod
    def base_transform():
        transform = vispy.visuals.transforms.AffineTransform()
        transform.rotate(3.0, (1, 0, 0))
        transform.scale((-1, 1, 1))
        transform.translate((0, 0.9, 0))
        return transform

class LidarMeshVisual(PointCloudMeshVisual):
    def __init__(self):
        super(LidarMeshVisual, self).__init__()

    @staticmethod
    def base_transform():
        transform = vispy.visuals.transforms.AffineTransform()
        transform.rotate(90, [1, 0, 0])
        transform.rotate(90, [0, 1, 0])
        transform.translate((0, 0.6, -2.5))
        return transform
