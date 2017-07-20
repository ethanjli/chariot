% Config_PlaneEstimation
debug_flag = 0;
save_debug_flag = 0;
show_WTA_result = 0;

%% parameters horizontal planes
HT = zeros(100,1);

d_scale_hori = 20; 
threshold_hori = 200; 
sigma_hori = 2/3;
n = 1; 

%% parameter for hough planes vertical
H = zeros(121,501);

max_dist = 15;
d_scale = (size(H,1)-1) / max_dist;
h = size(H,2);
index = 2;

threshold_nms = 150; 
sigma_vertical = 2;