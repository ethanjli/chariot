"""Classes for camera management."""
import numpy as np
import vispy.scene

from utilities import computation_chains

class CameraParameter(computation_chains.Parameter):
    def __init__(self, parameter_name):
        self.camera = None
        self.parameter_name = parameter_name
        self._last_updated_value = None
        super(CameraParameter, self).__init__()

    def register_camera(self, camera):
        self.camera = camera

    def get(self):
        return getattr(self.camera, self.parameter_name)

    def set(self, value):
        return setattr(self.camera, self.parameter_name, value)

    def update(self):
        if self._last_updated_value is None:
            self._last_updated_value = self.get()
        if self.source is None:
            return
        delta = np.array(self.get()) - np.array(self._last_updated_value)
        self._last_updated_value = np.array(self.source.get())
        self.set(delta + self._last_updated_value)
        self.updated()

    def reset(self):
        self._last_updated_value = None

class CameraParametersManager():
    def __init__(self, camera, camera_parameters):
        self._camera = camera
        parameters = {
            'fov': [
                ('base', computation_chains.ParameterOffset(
                    camera_parameters['fov'])),
                ('end', CameraParameter('fov'))
            ],
            'elevation': [
                ('base', computation_chains.ParameterOffset(
                    camera_parameters['elevation'])),
                ('head', computation_chains.ParameterOffset(0)),
                ('end', CameraParameter('elevation'))
            ],
            'azimuth': [
                ('base', computation_chains.ParameterOffset(
                    camera_parameters['azimuth'])),
                ('head', computation_chains.ParameterOffset(0)),
                ('end', CameraParameter('azimuth'))
            ],
            'distance': [
                ('base', computation_chains.ParameterOffset(
                    camera_parameters['distance'])),
                ('end', CameraParameter('distance'))
            ],
            'center': [
                ('base', computation_chains.ParameterOffset(
                    np.array(camera_parameters['center']))),
                ('end', CameraParameter('center'))
            ]
        }
        for chain in parameters.values():
            computation_chains.chain(*zip(*chain)[1])
        self.parameters = {name: dict(chain)
                           for (name, chain) in parameters.items()}

    def make_camera(self):
        initial_values = {name: chain['end'].source.get()
                          for (name, chain) in self.parameters.items()}
        initial_values['up'] = 'y'
        camera = vispy.scene.cameras.TurntableCamera(**initial_values)

        for chain in self.parameters.values():
            chain['end'].register_camera(camera)

        return camera

    def reset_all(self, camera_parameters):
        for (name, value) in camera_parameters.items():
            self.parameters[name]['base'].offset = value
            self.parameters[name]['end'].reset()
            self.parameters[name]['end'].update()

    def update_all(self):
        updated = False
        for chain in self.parameters.values():
            if chain['end'].needs_update():
                chain['end'].update()
                updated = True
        return updated

