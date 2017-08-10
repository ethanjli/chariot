import vispy.visuals

import point_cloud

class Visual(point_cloud.Visual):
    def __init__(self):
        super(Visual, self).__init__()

    @staticmethod
    def base_transform():
        transform = vispy.visuals.transforms.AffineTransform()
        transform.rotate(-90.0, (1, 0, 0))
        transform.translate((0, 1.5, 0))
        return transform
