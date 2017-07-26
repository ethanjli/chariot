from data import point_clouds
from rendering import canvas, scene
from unit._data.point_clouds import POINT_CLOUD_MAT_PATH

VIEW_PRESETS = scene.VIEW_PRESETS

scene_canvas = canvas.SceneCanvas(VIEW_PRESETS['1']['camera'])
scene_manager = scene.SceneManager(VIEW_PRESETS)
scene_manager.register_canvas(scene_canvas)

# Add visuals
scene_manager.add_visual('car')
scene_manager.add_visual('local')

# Load data
point_cloud = point_clouds.PointCloud()
point_cloud.load_from_mat(POINT_CLOUD_MAT_PATH)

# Render point cloud
scene_manager.point_clouds['local'].initialize_data(point_cloud.num_points)
scene_manager.point_clouds['local'].update_data(point_cloud)

scene_canvas.start_rendering()
