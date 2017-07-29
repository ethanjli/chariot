"""Classes representing point clouds."""
import scipy.io

class PointCloud(object):
    def __init__(self):
        self.points = None
        self.colors = None

    def load_from_mat(self, path):
        cloud = scipy.io.loadmat(path)['S'].T
        self.points = cloud[:, :3]
        self.colors = cloud[:, 3:]

    @property
    def num_points(self):
        return self.points.shape[0]

class Sequence(object):
    """Interface for point cloud sequences."""

    @property
    def num_points(self):
        return None

# PARALLEL LOADING

class PointCloudDoubleBuffer(DoubleBuffer):
    def __init__(self, num_components=2):
        super(PointCloudDoubleBuffer, self).__init__()
        self._point_cloud_bases = [[None for _ in range(num_components)],
                                   [None for _ in range(num_components)]]
        self._point_clouds = [[None for _ in range(num_components)],
                              [None for _ in range(num_components)]]
        self._num_points = [None, None]

    def initialize(self, ctype, shape):
        num_elements = reduce(operator.mul, shape, 1)

        self._locks = [multiprocessing.RLock(), multiprocessing.RLock()]

        self._point_cloud_bases[0] = [Array(ctype, num_elements, lock=self._locks[0])
                                      for _ in range(len(self._point_cloud_bases[0]))]
        self._point_cloud_bases[1] = [Array(ctype, num_elements, lock=self._locks[1])
                                      for _ in range(len(self._point_cloud_bases[1]))]

        self._point_clouds[0] = [as_array(base.get_obj()).reshape(*shape)
                                 for base in self._point_cloud_bases[0]]
        self._point_clouds[1] = [as_array(base.get_obj()).reshape(*shape)
                                 for base in self._point_cloud_bases[1]]

        self._num_points[0] = Value(ctypes.c_int, 0, lock=self._locks[0])
        self._num_points[1] = Value(ctypes.c_int, 0, lock=self._locks[1])

    @property
    def current_point_cloud(self):
        return self._point_clouds[self.current_id]

    @property
    def shadow_point_cloud(self):
        return self._point_clouds[self.shadow_id]

    @property
    def num_current_points(self):
        return self._num_points[self.current_id]

    @property
    def num_shadow_points(self):
        return self._num_points[self.shadow_id]

    def get_point_cloud(self, buffer_id):
        return self._point_clouds[buffer_id]

    def get_num_points(self, buffer_id):
        return self._num_points[buffer_id]

class PointCloudGenerator(LoaderGeneratorProcess):
    """Generates point clouds sequentially in a separate process into shared memory."""
    def __init__(self, *args, **kwargs):
        super(PointCloudGenerator, self).__init__(PointCloudDoubleBuffer(), *args, **kwargs)

        self._loader.load()  # Sometimes needed to calculate the array shape
        self._loader.stop_loading()  # We want to start the loader from our child process so we can join it
        self._loader.reset()
        self._buffer.initialize(self._loader.get_array_ctype(),
                                self._loader.get_array_shape())

    @property
    def time_range(self):
        return self._loader.time_range

    def get_times(self):
        return self._loader.get_times()

    # From LoaderGenerator

    def _on_load(self, loaded_next, target_buffer):
        num_points = loaded_next[0].shape[0]
        num_allowed_points = self.get_array_shape()[0]
        if num_points > num_allowed_points:
            print(self.__class__.__name__ + ' Warning: buffer can only hold ' +
                  str(num_allowed_points) + ' of the ' + str(num_points) +
                  ' points in the cloud!')
        num_points = min(num_points, num_allowed_points)
        self._buffer.get_num_points(target_buffer).value = num_points
        for (index, array) in enumerate(loaded_next):
            np.copyto(self._buffer.get_point_cloud(target_buffer)[index][:num_points],
                      array[:num_points])
        return None

    def _process_result(self, result):
        num_points = self._buffer.num_current_points.value
        return [array[:num_points] for array in self._buffer.current_point_cloud]

    def reset(self):
        super(PointCloudGenerator, self).reset()
        self._loader.reset()

    # From ArraySource

    def get_array_ctype(self):
        return self._loader.get_array_ctype()

    def get_array_shape(self):
        return self._loader.get_array_shape()

# POINT CLOUD AND MESH GENERATION

class MeshDoubleBuffer(PointCloudDoubleBuffer):
    def __init__(self, *args, **kwargs):
        super(MeshDoubleBuffer, self).__init__(*args, **kwargs)
        self._mesh_bases = [[None, None, None],
                            [None, None, None]]
        self._meshes = [[None, None, None],
                        [None, None, None]]
        self._num_vertices = [None, None]
        self._num_faces = [None, None]

    def initialize(self, array_ctypes, array_shapes):
        super(MeshDoubleBuffer, self).initialize(array_ctypes[0], array_shapes[0])

        num_vertices = reduce(operator.mul, array_shapes[1], 1)
        num_faces = reduce(operator.mul, array_shapes[2], 1)
        self._mesh_bases[0] = [Array(array_ctypes[1], num_vertices, lock=self._locks[0]),
                               Array(array_ctypes[1], num_vertices, lock=self._locks[0]),
                               Array(array_ctypes[2], num_faces, lock=self._locks[0])]
        self._mesh_bases[1] = [Array(array_ctypes[1], num_vertices, lock=self._locks[1]),
                               Array(array_ctypes[1], num_vertices, lock=self._locks[1]),
                               Array(array_ctypes[2], num_faces, lock=self._locks[1])]

        self._meshes[0] = [as_array(self._mesh_bases[0][0].get_obj()).reshape(*array_shapes[1]),
                           as_array(self._mesh_bases[0][1].get_obj()).reshape(*array_shapes[1]),
                           as_array(self._mesh_bases[0][2].get_obj()).reshape(*array_shapes[2])]
        self._meshes[1] = [as_array(self._mesh_bases[1][0].get_obj()).reshape(*array_shapes[1]),
                           as_array(self._mesh_bases[1][1].get_obj()).reshape(*array_shapes[1]),
                           as_array(self._mesh_bases[1][2].get_obj()).reshape(*array_shapes[2])]

        self._num_vertices[0] = Value(ctypes.c_int, 0, lock=self._locks[0])
        self._num_vertices[1] = Value(ctypes.c_int, 0, lock=self._locks[1])
        self._num_faces[0] = Value(ctypes.c_int, 0, lock=self._locks[0])
        self._num_faces[1] = Value(ctypes.c_int, 0, lock=self._locks[1])

    @property
    def current_mesh(self):
        return self._meshes[self.current_id]

    @property
    def shadow_mesh(self):
        return self._meshes[self.shadow_id]

    @property
    def num_current_vertices(self):
        return self._num_vertices[self.current_id]

    @property
    def num_shadow_vertices(self):
        return self._num_vertices[self.shadow_id]

    @property
    def num_current_faces(self):
        return self._num_faces[self.current_id]

    @property
    def num_shadow_faces(self):
        return self._num_faces[self.shadow_id]

    def get_mesh(self, buffer_id):
        return self._meshes[buffer_id]

    def get_num_vertices(self, buffer_id):
        return self._num_vertices[buffer_id]

    def get_num_faces(self, buffer_id):
        return self._num_faces[buffer_id]

class PointCloudMesher(LoaderGeneratorProcess):
    """Generates and meshes point clouds sequentially in a separate process into shared memory.
    Note: _on_load currently assumes that the point cloud consists of exactly two arrays."""
    def __init__(self, *args, **kwargs):
        super(PointCloudMesher, self).__init__(MeshDoubleBuffer(), *args, **kwargs)

        self._loader.load()  # Sometimes needed to calculate the array shape
        self._loader.stop_loading()  # We want to start the loader from our child process so we can join it
        self._loader.reset()
        self._buffer.initialize(self._loader.get_array_ctypes(),
                                self._loader.get_array_shapes())

    @property
    def time_range(self):
        return self._loader.time_range

    def get_times(self):
        return self._loader.get_times()

    # From LoaderGenerator

    def _on_load(self, loaded_next, target_buffer):
        # Point cloud
        num_points = loaded_next[0].shape[0]
        num_allowed_points = self.get_array_shapes()[0][0]
        if num_points > num_allowed_points:
            print(self.__class__.__name__ + ' Warning: buffer can only hold ' +
                  str(num_allowed_points) + ' of the ' + str(num_points) +
                  ' points in the cloud!')
        num_points = min(num_points, num_allowed_points)
        self._buffer.get_num_points(target_buffer).value = num_points
        # This is the section which assumes exactly two arrays in the point cloud part
        np.copyto(self._buffer.get_point_cloud(target_buffer)[0][:num_points],
                  loaded_next[0][:num_points])
        np.copyto(self._buffer.get_point_cloud(target_buffer)[1][:num_points],
                  loaded_next[1][:num_points])

        # Mesh
        num_vertices = loaded_next[2].shape[0]
        num_allowed_vertices = self.get_array_shapes()[1][0]
        if num_vertices > num_allowed_vertices:
            print(self.__class__.__name__ + ' Warning: buffer can only hold ' +
                  str(num_allowed_vertices) + ' of the ' + str(num_vertices) +
                  ' vertices in the mesh!')
        num_vertices = min(num_vertices, num_allowed_vertices)
        self._buffer.get_num_vertices(target_buffer).value = num_vertices
        np.copyto(self._buffer.get_mesh(target_buffer)[0][:num_vertices],
                  loaded_next[2][:num_vertices])
        np.copyto(self._buffer.get_mesh(target_buffer)[1][:num_vertices],
                  loaded_next[3][:num_vertices])
        num_faces = loaded_next[4].shape[0]
        num_allowed_faces = self.get_array_shapes()[2][0]
        if num_faces > num_allowed_faces:
            print(self.__class__.__name__ + ' Warning: buffer can only hold ' +
                  str(num_allowed_faces) + ' of the ' + str(num_faces) +
                  ' faces in the mesh!')
        num_faces = min(num_faces, num_allowed_faces)
        self._buffer.get_num_faces(target_buffer).value = num_faces
        np.copyto(self._buffer.get_mesh(target_buffer)[2][:num_faces],
                  loaded_next[4][:num_faces])
        return None

    def _process_result(self, result):
        # Point cloud
        num_points = self._buffer.num_current_points.value
        arrays = [array[:num_points] for array in self._buffer.current_point_cloud]

        # Mesh
        num_vertices = self._buffer.num_current_vertices.value
        num_faces = self._buffer.num_current_faces.value
        mesh = self._buffer.current_mesh
        arrays.extend([mesh[0][:num_vertices], mesh[1][:num_vertices], mesh[2][:num_faces]])
        return arrays

    def reset(self):
        super(PointCloudMesher, self).reset()
        self._loader.reset()

    # From ArraysSource

    def get_array_ctypes(self):
        return self._loader.get_array_ctypes()

    def get_array_shapes(self):
        return self._loader.get_array_shapes()

