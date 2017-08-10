from os import path
import time

import scipy.misc
import vispy.app
import vispy.gloo

from utilities import files
from datasets import datasets, omnistereo
from rendering import scene

VIEW_PRESETS = scene.VIEW_PRESETS

OUTPUT_PATH = path.join(datasets.DATASETS_PATH, 'Chariot_' + time.strftime('%Y%m%d'))

class Animator(scene.SceneAnimator):
    def __init__(self):
        super(Animator, self).__init__()
        self.dataset = omnistereo.Dataset('Omnicam_04-Aug-2017')
        self.sequence = self.dataset.sequences['point_cloud']['raw']['files']
        self.point_cloud_loader = omnistereo.PointCloudSequenceConcurrentLoader(self.sequence)
        self.screenshot_counter = 0

    def register_canvas(self, canvas):
        super(Animator, self).register_canvas(canvas)
        self.scene_manager.register_canvas(canvas)
        self.init_car_visual()
        self.init_point_cloud_visual('omni', self.sequence, max_num_points=300000)
        files.make_dir_path(OUTPUT_PATH)
        self.point_cloud_loader.load()
        canvas.register_timer_observer(self)

    def execute(self, event):
        try:
            self.update_point_cloud('omni', next(self.point_cloud_loader))
            self.scene_manager.execute(event)

            screenshot = vispy.gloo.util._screenshot()
            scipy.misc.imsave(path.join(OUTPUT_PATH, str(self.screenshot_counter)) + '.png', screenshot)
            self.screenshot_counter += 1
        except StopIteration:
            print('Finishing up...')
            vispy.app.quit()
            self.point_cloud_loader.reset()
            return

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

