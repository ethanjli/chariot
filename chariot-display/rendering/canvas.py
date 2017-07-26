"""Classes for rendering visuals."""
import numpy as np
import vispy.app
import vispy.scene
import vispy.visuals

from visuals import visuals
from rendering import camera

_PIXEL_KEYS = {}

class SceneCanvas(vispy.scene.SceneCanvas):
    """Manages rendering of 3-D point cloud data."""
    def __init__(self, camera_parameters, background_color='white'):
        super(SceneCanvas, self).__init__(
            keys='interactive', size=(800, 600), bgcolor=background_color)

        self.visual_nodes = {}
        self._key_press_observers = []
        self.timer_observers = []
        self._timers = []
        self._window_scale = 1.0
        self.transformSystem = vispy.visuals.transforms.TransformSystem(self)

        self._view = self.central_widget.add_view()
        self.camera = camera.CameraParametersManager(self._view.camera, camera_parameters)
        self._view.camera = self.camera.make_camera()
        self._add_axes()

        # Custom text visuals
        self._texts = []
        self._available_text_position = np.array([5, 5])

    # Initialization
    def _add_axes(self):
        self._axes = vispy.scene.visuals.XYZAxis(parent=self.get_scene())
        self._axes.transform = vispy.visuals.transforms.AffineTransform()
        self._axes.transform.scale((5, 5, 5))

    # Rendering
    def start_rendering(self):
        for timer in self._timers:
            timer.start()
        self.update()
        self.show()
        vispy.app.run()

    def instantiate_visual(self, Visual, name, *args, **kwargs):
        VisualNode = visuals.create_visual_node(Visual)
        visual_node = VisualNode(*args, parent=self.get_scene(), **kwargs)
        self.visual_nodes[name] = visual_node
        visual_node.update_transform(visual_node.apply_final_transform(
            visual_node.base_transform()))
        visual_node.update_scale(self.pixel_scale)
        return visual_node

    def add_text(self, text):
        self._texts.append(text)
        text.set_position(self._available_text_position)
        self._available_text_position[1] += 5 + text.get_size()

    # Utility
    def get_scene(self):
        return self._view.scene

    def get_scale(self):
        # TODO: 30.0 is a magic number, get rid of it
        return (self._window_scale * 30.0 /
                self.camera.parameters['fov']['end'].get() *
                self.camera.parameters['distance']['base'].offset /
                self.camera.parameters['distance']['end'].get())

    def _update_scale(self):
        for (_, visual_node) in self.visual_nodes.items():
            visual_node.update_scale(self.get_scale())

    # Event loops
    def register_timer_observer(self, timer_observer):
        self.timer_observers.append(timer_observer)
        timer = vispy.app.Timer('auto', connect=timer_observer.execute)
        self._timers.append(timer)

    # Event Handlers
    def on_resize(self, event):
        self._window_scale = self._window_scale * self.size[1] / self._central_widget.size[1]
        self._update_scale()
        super(SceneCanvas, self).on_resize(event)

    def on_mouse_wheel(self, event):
        self._update_scale()

    def on_draw(self, event):
        for text in self._texts:
            text.update()
        super(SceneCanvas, self).on_draw(event)

    def register_key_press_observer(self, key_press_observer):
        self._key_press_observers.append(key_press_observer)

    def on_key_press(self, event):
        for observer in self._key_press_observers:
            observer.on_key_press(event)
        if event.text == ' ':
            for timer in self._timers:
                if timer.running:
                    timer.stop()
                else:
                    timer.start()
                # TODO: also pause reconstruction
        elif event.text in _PIXEL_KEYS:
            self._on_key_press_pixel_size(event)

    def set_visibility(self, visual_node, visibility):
        self.visual_nodes[visual_node].visible = visibility

    def _on_key_press_pixel_size(event):
        # TODO: implement this!
        pass
