from os import path
import time

import scipy.misc
import vispy.app
import vispy.gloo

from utilities import files
from datasets import datasets, point_clouds, video_popup
from rendering import scene

VIEW_PRESETS = scene.VIEW_PRESETS

OUTPUT_PATH = path.join(datasets.DATASETS_PATH, 'Chariot_' + time.strftime('%Y%m%d'))

class Animator(scene.SceneAnimator):
    def __init__(self):
        super(Animator, self).__init__()
        #self.dataset = video_popup.KittiDataset('VideoPopup_kitti_05_new')
        #self.dataset = video_popup.LogC920x1Dataset('VideoPopup/0/DepthReconstruction/pc/DenseLinear/')
        self.typ = 'DenseNearest'
        self.label = 'dense_nearest'
        self.dataset_left = video_popup.LogC920x1Dataset('/home/cvfish/Work/code/bitbucket/video_popup/results/DepthReconstructionLeft/PointClouds/'+self.typ)
        self.dataset_front = video_popup.LogC920x1Dataset('/home/cvfish/Work/code/bitbucket/video_popup/results/DepthReconstructionFront/PointClouds/'+self.typ)
        self.dataset_right = video_popup.LogC920x1Dataset('/home/cvfish/Work/code/bitbucket/video_popup/results/DepthReconstructionRight/PointClouds/'+self.typ)
        #self.sequence = self.dataset.sequences['point_cloud']['dense_global']['files']
        self.sequence_left = self.dataset_left.sequences['point_cloud'][self.label]['files']
        self.sequence_front = self.dataset_front.sequences['point_cloud'][self.label]['files']
        self.sequence_right = self.dataset_right.sequences['point_cloud'][self.label]['files']
        self.point_cloud_loader_left = point_clouds.SequenceConcurrentLoader(self.sequence_left)
        self.point_cloud_loader_front = point_clouds.SequenceConcurrentLoader(self.sequence_front)
        self.point_cloud_loader_right = point_clouds.SequenceConcurrentLoader(self.sequence_right)
        self.screenshot_counter = 0

    def register_canvas(self, canvas):
        super(Animator, self).register_canvas(canvas)
        self.scene_manager.register_canvas(canvas)
        self.init_car_visual()
        self.init_point_cloud_visual('right', self.sequence_right, max_num_points=600000)
        files.make_dir_path(OUTPUT_PATH)
        self.point_cloud_loader_right.load()
        self.init_point_cloud_visual('front', self.sequence_front, max_num_points=600000)
        files.make_dir_path(OUTPUT_PATH)
        self.point_cloud_loader_front.load()
        self.init_point_cloud_visual('left', self.sequence_left, max_num_points=600000)
        files.make_dir_path(OUTPUT_PATH)
        self.point_cloud_loader_left.load()
        canvas.register_timer_observer(self)

    def execute(self, event):
        try:
	    pc = next(self.point_cloud_loader_right)
            self.update_point_cloud('right', pc)
	    pc = next(self.point_cloud_loader_front)
            self.update_point_cloud('front', pc)
	    pc = next(self.point_cloud_loader_left)
	    self.update_point_cloud('left', pc)
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

