"""Classes for scene management."""
import itertools

from utilities import profiling, concurrency
from visuals import mesh, point_cloud, text
import canvas

VISUAL_NAMES = ['car', 'local']
VISUALS = {
    'car': {
        'type': 'mesh',
        'class': mesh.CarModelVisual
    },
    'local': {
        'type': 'point_cloud',
        'class': point_cloud.LocalVisual,
        'framerate_counter': {
            'name': 'local data',
            'units': 'updates/sec'
        }
    },
    'global': {
        'type': 'point_cloud',
        'class': point_cloud.GlobalVisual,
        'framerate_counter': {
            'name': 'global data',
            'units': 'updates/sec'
        }
    },
    'front': {
        'type': 'image',
    }
}
VISIBILITY_KEYS = {
    'a': 'car',
    's': 'local',
    'd': 'global'
}

VIEW_PRESETS = {
    '1': {  # Elevated third-person view
        'camera': {   # Camera parameters
            'fov': 30,
            'elevation': 15,
            'azimuth': 90,
            'distance': 20,
            'center': (0, 0.9, 1.2)
        },
        'visuals': {   # Visual visibility
            'car': True
        }
    },
    '2': {  # Driver's seat first-person view
        'camera': {   # Camera parameters
            'fov': 30,
            'elevation': -10,
            'azimuth': 90,
            'distance': 0.75,
            'center': (0.5, 0.6, -1.2)
        },
        'visuals': {   # Visual visibility
            'car': False
        }
    }
}

def DefaultCanvas():
    return canvas.SceneCanvas(VIEW_PRESETS['1']['camera'])

class SceneManager():
    """Manages customizable aspects of the visuals scene."""
    def __init__(self, presets):
        self._canvas = None
        self._presets = presets

        self.point_clouds = {
            'local': None,
            'global': None
        }
        self.meshes = {
            'car': None
        }
        self.images = {
            ('mono_preprocessed', 'left'): None,
            ('mono_preprocessed', 'right'): None
        }

        self._visibilities = {visual_name: False for visual_name in VISUALS}

    def register_canvas(self, scene_canvas, register_updater=True):
        self._canvas = scene_canvas
        self._canvas.register_key_press_observer(self)
        if register_updater:
            self._canvas.register_timer_observer(self)

        self.framerate_counter = profiling.FramerateCounter()
        framerate_counter = text.FramerateCounter(
            self._canvas, self.framerate_counter, 'render', 'redraws/sec')
        self._canvas.add_text(framerate_counter)

        self._camera = self._canvas.camera

    # Visual Instantiation

    def add_visual(self, visual_name):
        visual_params = VISUALS[visual_name]
        if visual_params['type'] == 'image':
            return
        if visual_params['type'] == 'mesh':
            target = self.meshes
        elif visual_params['type'] == 'point_cloud':
            target = self.point_clouds
        target[visual_name] = self._canvas.instantiate_visual(
            visual_params['class'], visual_name)
        if 'framerate_counter' in visual_params:
            framerate_counter = text.FramerateCounter(
                self._canvas, target[visual_name].framerate_counter,
                visual_params['framerate_counter']['name'],
                visual_params['framerate_counter']['units'])
            self._canvas.add_text(framerate_counter)
        self._visibilities[visual_name] = True

    # Visual Initialization

    def init_point_cloud(self, visual_name, source):
        self.point_clouds[visual_name].initialize_data(
            source.get_array_shape()[0])

    def init_mesh(self, visual_name, num_vertices, num_faces):
        self.meshes[visual_name].initialize_data(num_vertices, num_faces)

    def init_image(self, visual_name, image_drawer):
        self.images[visual_name] = image_drawer

    # Event Handlers

    def on_key_press(self, event):
        if event.text in VISIBILITY_KEYS:
            self.toggle_visibility(VISIBILITY_KEYS[event.text])
        elif event.text in self._presets:
            self.apply_preset(self._presets[event.text])

    def toggle_visibility(self, visual_name, new_visibility=None):
        try:
            if new_visibility is None:
                new_visibility = not self._visibilities[visual_name]
            self._canvas.set_visibility(visual_name, new_visibility)
            self._visibilities[visual_name] = new_visibility
        except KeyError:
            print('SceneManager Warning: No "' + visual_name +
                  '" visual in the SceneCanvas!')

    def apply_preset(self, preset):
        self._camera.reset_all(preset['camera'])
        for (visual_node, display) in preset['visuals'].items():
            self._canvas.set_visibility(visual_node, display)

    def execute(self, event):
        updated = False

        # Update visuals
        for visual in itertools.chain(self.point_clouds.values(),
                                      self.meshes.values()):
            if visual is not None and visual.updated_state:
                visual.redraw()
                updated = True
        for image in self.images.values():
            if image is not None and image.updated_state:
                image.redraw()

        # Update camera
        updated = self._camera.update_all() or updated

        if updated:
            self._canvas.update()
            self.framerate_counter.tick()

class SceneAnimator(concurrency.Thread):
    """Abstract class for animating a scene."""
    def __init__(self, view_presets=VIEW_PRESETS):
        super(SceneAnimator, self).__init__()
        self.canvas = None
        self.scene_manager = SceneManager(view_presets)

    # Rendering initialization helpers

    def register_canvas(self, scene_canvas, register_updater=True):
        self.canvas = scene_canvas
        self.scene_manager.register_canvas(scene_canvas, register_updater)

    def init_car_visual(self):
        self.scene_manager.add_visual('car')

    def init_local_visual(self, point_cloud_sequence, max_num_points=None, points_margin=1000):
        self.scene_manager.add_visual('local')
        if max_num_points is None:
            max_num_points = point_cloud_sequence.num_points + points_margin
        self.scene_manager.point_clouds['local'].initialize_data(max_num_points)

    # Rendering update helpers

    def update_local(self, point_cloud):
        self.scene_manager.point_clouds['local'].update_data(point_cloud)

