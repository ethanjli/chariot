from data import point_clouds
from rendering import canvas, scene
from tests.unit._data.point_clouds import FRONT_MAT_PATH

VIEW_PRESETS = scene.VIEW_PRESETS

scene_canvas = canvas.SceneCanvas(VIEW_PRESETS['1']['camera'])
scene_manager = scene.SceneManager(VIEW_PRESETS)
scene_manager.register_canvas(scene_canvas)

# Add visuals
scene_manager.add_visual('car')
scene_manager.add_visual('front')

# Load data
point_cloud = point_clouds.PointCloud()
point_cloud.load_from_mat(FRONT_MAT_PATH, 'points')

# Render point cloud
scene_manager.point_clouds['front'].initialize_data(point_cloud.num_points)
scene_manager.point_clouds['front'].update_data(point_cloud)

scene_canvas.start_rendering()
