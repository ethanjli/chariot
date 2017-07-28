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

