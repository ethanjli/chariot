from data import point_clouds
from rendering import canvas, scene
#from tests.unit._data.point_clouds import FRONT_MAT_PATH
#FRONT_MAT_PATH = '/home/tj/Data/points'
FRONT_MAT_PATH = '/home/cvfish/Work/code/bitbucket/video_popup/results/DepthReconstruction/PointClouds/DenseNearest/points_dense_nearest_1090'
VIEW_PRESETS = scene.VIEW_PRESETS

scene_canvas = canvas.SceneCanvas(VIEW_PRESETS['1']['camera'])
scene_manager = scene.SceneManager(VIEW_PRESETS)
scene_manager.register_canvas(scene_canvas)

# Add visuals
scene_manager.add_visual('car')
scene_manager.add_visual('right')

# Load data
point_cloud = point_clouds.PointCloud()
point_cloud.load_from_mat(FRONT_MAT_PATH, 'points', color_type='uint8')


# Render point cloud
scene_manager.point_clouds['right'].initialize_data(point_cloud.num_points)
scene_manager.point_clouds['right'].update_data(point_cloud)

scene_canvas.start_rendering()
