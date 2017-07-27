from datasets import omnistereo
from rendering import scene

VIEW_PRESETS = scene.VIEW_PRESETS

class Animator(scene.SceneAnimator):
    def __init__(self):
        super(Animator, self).__init__()
        self.dataset = omnistereo.Dataset('Results_20-Jul-2017')
        self.sequence = self.dataset.sequences['point_cloud']['raw']['files']
        self.point_clouds = self.sequence.point_clouds

    def register_canvas(self, canvas):
        super(Animator, self).register_canvas(canvas)
        self.scene_manager.register_canvas(canvas)
        self.init_car_visual()
        self.init_local_visual(self.sequence)
        self.run_async()

    def execute(self):
        try:
            self.update_local(next(self.point_clouds))
        except StopIteration:
            print('Done, repeating animation.')
            self.point_clouds = self.sequence.point_clouds

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

