from datasets import point_clouds, video_popup
from rendering import scene

VIEW_PRESETS = scene.VIEW_PRESETS

class Animator(scene.SceneAnimator):
    def __init__(self):
        super(Animator, self).__init__()
        self.dataset = video_popup.KittiDataset('VideoPopup_kitti_05')
        self.sequence = self.dataset.sequences['point_cloud']['dense_linear']['files']
        self.point_cloud_loader = point_clouds.SequenceLoader(self.sequence)

    def register_canvas(self, canvas):
        super(Animator, self).register_canvas(canvas)
        self.scene_manager.register_canvas(canvas)
        self.init_car_visual()
        self.init_point_cloud_visual('front', self.sequence, max_num_points=500000)
        self.run_concurrent()

    def execute(self):
        try:
            self.update_point_cloud('front', next(self.point_cloud_loader))
        except StopIteration:
            print('Done, repeating animation.')
            self.point_cloud_loader.reset()

    def on_run_finish(self):
        pass


def main():
    canvas = scene.DefaultCanvas()
    animator = Animator()
    animator.register_canvas(canvas)
    canvas.start_rendering()
    animator.terminate()


if __name__ == '__main__':
    main()
