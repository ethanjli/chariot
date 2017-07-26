import os
import sys

import vispy.io
import vispy.visuals
import vispy.scene

_PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))
SHADERS_FOLDER = 'shaders'
MODELS_FOLDER = 'models'

class CustomVisual(vispy.visuals.Visual):
    def __init__(self):
        super(CustomVisual, self).__init__()
        self.transform_update = None
        self.updated_state = False

    @staticmethod
    def base_transform():
        return vispy.visuals.transforms.AffineTransform()

    @staticmethod
    def apply_final_transform(transform):
        return transform

    def update_scale(self, pixel_scale):
        pass

    def update_transform(self, transform):
        self.transform_update = transform
        self.updated_state = True

    def redraw(self):
        if self.updated_state:
            self.transform = self.transform_update
            self.updated_state = False

class ShadedVisual(CustomVisual):
    def __init__(self, vertex_shader_filename, fragment_shader_filename):
        super(ShadedVisual, self).__init__()
        self.program = load_shader_program(vertex_shader_filename,
                                           fragment_shader_filename)

    def bind_transforms(self, transforms):
        visual_to_doc = transforms.visual_to_document
        self.program.vert['visual_to_doc'] = visual_to_doc
        doc_to_render = transforms.framebuffer_to_render * transforms.document_to_framebuffer
        self.program.vert['doc_to_render'] = doc_to_render


    def set_param(self, key, value):
        self.program[key] = value

    def set_vert_param(self, key, value):
        self.program.vert[key] = value

    def set_frag_param(self, key, value):
        self.program.frag[key] = value


def load_shader(shader_filename):
    with open(os.path.join(_PACKAGE_PATH, SHADERS_FOLDER, shader_filename), 'r') as f:
        shader = f.read()
    return shader

def load_shader_program(vertex_shader_filename, fragment_shader_filename):
    vertex_shader = load_shader(vertex_shader_filename)
    fragment_shader = load_shader(fragment_shader_filename)
    return vispy.visuals.shaders.ModularProgram(vertex_shader, fragment_shader)

def load_model(mesh_name):
    mesh_filename = os.path.join(_PACKAGE_PATH, MODELS_FOLDER, mesh_name)
    return vispy.io.read_mesh(mesh_filename)

def create_visual_node(Visual):
    return vispy.scene.visuals.create_visual_node(Visual)
