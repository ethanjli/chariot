import vispy.visuals

import point_cloud

class FrontVisual(point_cloud.Visual):
    def __init__(self):
        super(FrontVisual, self).__init__()

    @staticmethod
    def base_transform():
        transform = vispy.visuals.transforms.AffineTransform()
        transform.translate((0, 1.5, 0))
        return transform

