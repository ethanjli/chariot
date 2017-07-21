% Config for Rectification
opts = init();
%% Parameter
maske_stereo = imread(sprintf('%s/data/Masks/Maske_Stereo1.png',opts.data_dir));

% Calibration Methods Rectification 
calib_stereo = 14;
calib_motion = 14;

colored_rectified = 1; %if 1 = gray, else color;

% alg = 1 == BM und alg = 2 == SGBM
alg = 2;
if alg == 1
    alg_name = 'BM';
    savename_pointcloud = 'point_cloudBM';
    savename_image = 'dispBM';
else
    alg_name = '';
    savename_pointcloud = 'point_cloud';
    savename_image = 'disp';
end

% Interpolation Method
inter = 'linear';

estimate_point_cloud = 1;
save_point_cloud = 0;
save_point_cloud_mat = 0;
save_image = 1;


%% Values for rectified stereo images (left/right)
    thetaS.start = 70 / 360 * 2 * pi; 
    thetaS.end =  290 / 360 * 2 * pi; 
    thetaS.length = 1400;
    
    phiS.start = 1;
    phiS.end = 1000;
    phiS.length = 1000;
    
    border1 = 430; 
    border2 = 830;




% Values for rectified images
thetaML.start = 30 / 360 * 2 * pi; 
thetaML.end =   105/ 360 * 2 * pi; 
thetaML.length = 500;

thetaMR.start = 255 / 360 * 2 * pi;
thetaMR.end =   330 / 360 * 2 * pi;
thetaMR.length = 500;


phiM.start = 1;
phiM.end = 700;
phiM.length = 700;

%% Values for the 3D reconstruction
% Area in which the image points are reconstructed
point_num = 1;      % number of the n-th point  
% Stereo
StereoMinOben = 50;
StereoMaxOben = 300;
StereoMinUnten = 1000;
StereoMaxUnten = 1350;
StereoCloud = [ StereoMinOben : point_num : StereoMaxOben, StereoMinUnten : point_num : StereoMaxUnten];

% Motion Left
LeftMin = 2;
LeftCloud = [ 1 : point_num :  thetaML.length];

% Motion Right
RightMax = 500;
RightCloud = [ 1 : point_num : thetaML.length ];

distance_max = 25; % m

