from data.point_clouds import ParallelLoader
from datasets.point_clouds import SequenceConcurrentLoader
from datasets import omnistereo
from rendering import scene

VIEW_PRESETS = scene.VIEW_PRESETS

class Animator(scene.SceneAnimator):
    def __init__(self):
        super(Animator, self).__init__()
        self.dataset = omnistereo.Dataset('Omnicam_04-Aug-2017')
        self.sequence = self.dataset.sequences['point_cloud']['raw']['files']
        self.point_cloud_loader = ParallelLoader(
            lambda: SequenceConcurrentLoader(
                self.sequence, max_num_points=300000))

    def register_canvas(self, canvas):
        super(Animator, self).register_canvas(canvas)
        self.scene_manager.register_canvas(canvas)
        self.init_car_visual()
        self.init_point_cloud_visual('omni', self.sequence, max_num_points=300000)
        self.point_cloud_loader.load()
        self.run_concurrent()

    def execute(self):
        try:
            self.update_point_cloud('omni', next(self.point_cloud_loader))
        except StopIteration:
            print('Done, repeating animation in 2 seconds.')
            self.point_cloud_loader.reset()
            self.point_cloud_loader.load()

    def on_run_finish(self):
        self.point_cloud_loader.stop_loading()

def main():
    canvas = scene.DefaultCanvas()
    animator = Animator()
    animator.register_canvas(canvas)
    canvas.start_rendering()
    animator.terminate()


if __name__ == '__main__':
    main()

