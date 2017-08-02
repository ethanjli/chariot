%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function run_reconstruction ()

clear all; close all; clc;

opts = init();
root_dir = opts.root_dir;
data_dir = opts.data_dir;

img_folder = opts.img_folder;
calibration_path = sprintf('%s/data/Calib/', data_dir);
saveFolder = sprintf('%s/data/Results_%s/',data_dir, date);

% Sequenz or single images
seq_or_single = 1;                                      % 1-sequenz /2-single
nums1 = 1;
extract_plane_flag = 1;

if seq_or_single == 1
    seq = 8;                                            % Seq No
    begin_frame = 5000;
    end_frame = 5019;
elseif seq_or_single == 2
    %load(sprintf('%sResultAll/F2.mat', saveFolder));    % Single Folder
    load(sprintf('%s/data/F2.mat',data_dir));
    F = F2;     
    %seq = F(m,1);                                             % Seq No
    begin_frame = 1;
    end_frame = size(F,1);
end

if seq_or_single == 1
    name = sprintf('2013_05_14_drive_%04d_sync', seq);      % Sequenz Name
    save_folder = sprintf('%sSeq_%04d', saveFolder, seq);
    mkdir(save_folder)
end
    
for m = begin_frame : nums1 : end_frame
    
    if seq_or_single == 1
        frame_number = m;                                   % Frame No

    elseif seq_or_single == 2
        frame_number = F(m,2);                              % Frame No
        seq = F(m,1);
        name = sprintf('2013_05_14_drive_%04d_sync', seq);      % Sequenz Name
        save_folder = sprintf('%sSeq_%04d', saveFolder, seq);
        mkdir(save_folder)
    end
    
    fprintf('Start Plane Estimation for Seq %02d / Frame Number %06d.\n', seq, frame_number);
    tStart=tic; 
    run_reconstruction_func ( save_folder, seq, frame_number, calibration_path, name, img_folder, extract_plane_flag );
    end_time = toc(tStart);
    fprintf('Time for one frame: %s seconds. \n', end_time);
end

end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function run_reconstruction_func( save_folder, seq, frame_number, calibration_path, name, img_folder, extract_plane_flag )

show_results = 0;
%% Run Motion Estimation
fprintf( '========== MOTION =================\n' );
tic;

fprintf( 'Run Motion Estimation for Seq %d, Frame %d: \n', seq, frame_number);

M1 = MotionEstimationSeq ( seq, frame_number, frame_number, save_folder, calibration_path, name );

toc;
fprintf( '============ DONE =================\n' );        

%% Run Rectifacation and Save Point Cloud
fprintf( '========== RECTIFICATION ==================\n' );
tic;

config_rectification;
point_cloud_stereo_first    = sprintf('%s/Rectification/point_cloud_stereo%s_%06d.mat', save_folder, alg_name, frame_number);

if (exist( point_cloud_stereo_first) ~= 2 ) % for stereo frame_number 
    S1 = run_stereo_estimation ( frame_number, img_folder, name, calibration_path, save_folder, 2, 3, M1);
else
    load( point_cloud_stereo_first);
    S1 = S;
end

S2 = run_stereo_estimation ( frame_number+1, img_folder, name, calibration_path, save_folder, 2, 3, M1);
S_left = run_stereo_estimation ( frame_number, img_folder, name, calibration_path, save_folder, 2, 2, M1);
S_right = run_stereo_estimation ( frame_number, img_folder, name, calibration_path, save_folder, 3, 3, M1);

H = [ rodrigues( M1(4:6,:)), M1(1:3,:)./1000; 0,0,0,1];
H_ = inv( H ); 

S22 = [S2(1:3,:)];
S22(4,:) = 1;
        
S22 = H_ * S22; 
if size(S2,1) == 6
    S22(4:6,:) = S2(4:6,:);
else
    S22(4,:) = S2(4,:);
end

S = [S1, S22, S_left, S_right];

toc;
fprintf( '=============== DONE ====================\n' );

%% run calculation 360° disparity image
fprintf( '========== 360 STEREO ==================\n' );
tic;

config_360_stereo_image;

% compute disparity image
save_folder_disp2 = sprintf('%s/Stereo_Disp/Frame_%06d/', save_folder, frame_number);
save_folder_disp = sprintf('%s/Stereo_Disp/', save_folder);
mkdir(save_folder_disp);
filename_stereo = sprintf('%sIdis%s_%06d.mat', save_folder_disp, alg_name, frame_number);
    
% compute coordinate system between all cameras
load(sprintf('%scalib_0014.mat',calibration_path));
Hex = [ rodrigues(param.cam{2}.ex_om), param.cam{2}.ex_T; 0 0 0 1];
Hm = [ rodrigues( M1(4:6,:)), M1(1:3,:); 0,0,0,1];

KS1 = param.cam{1}.ex_T;
KS2 = param.cam{2}.ex_T;
KS3 = M1(1:3);
Ks4 = Hex * Hm;
KS4 = Ks4(1:3,4);
best_KS = median([KS1, KS2, KS3, KS4]')'./1000;

S_ks = S(1:3,:) + repmat(best_KS,1,size(S,2));

% Estimate Road Plane
plane = roadPlaneMex( S_ks );
Tr_plane_camera = roadPlaneToCamera(plane);
R_plane_camera = Tr_plane_camera(1:3,1:3);
R_camera_plane = inv(R_plane_camera);

S_ks2 = R_camera_plane*S_ks;

if size(S,1) == 6
    S_ks2(4:6,:) =S(4:6,:); 
else
    S_ks2(4,:) =S(4,:); 
end

[ Idis, Img_new, phi, theta] = new_disparity_image (S_ks2, save_folder_disp, frame_number, width, height, max_visible_theta, ...
    alg_name, minTheta, maxTheta, 0);

if show_results
    
    figure(1);
    imagesc(Idis);
    figure(2);
    imagesc(Img_new);
    
end

if save_debug_flag
    mkdir(save_folder_disp2);
    save( sprintf('%sIdis%s.mat', save_folder_disp2, alg_name), 'Idis','theta');
    save( sprintf('%sR_camera_plane%s.mat', save_folder_disp2, alg_name), 'R_camera_plane');
end

toc;
fprintf( '=============== DONE ====================\n' );


%% Compute Superpixel (mex)
fprintf( '========== SUPERPIXEL ==================\n' );
tic;

% compute Superpixel 
Islic_name = sprintf('%sIslic_%06d.png', save_folder_disp, frame_number);                           
Img_name = sprintf('%sImg_%06d.png', save_folder_disp, frame_number);                              
Idis_name = sprintf('%sIdis_%06d.png', save_folder_disp, frame_number);                            
t = [sprintf('%s/StereoSlic/stereoslic ', opts.root_dir) '-o ', Islic_name, ' ', Img_name, ' ', Idis_name];  
unix(t);                                                                                            
                                                                                                    
SP_file = sprintf('%sIslic_%06d.png',save_folder_disp, frame_number);                               %
SP = (imread(SP_file) + 1);   

%[SP, contour] = superpixel_mex(uint8(round(Img_new.*255)), 1000, 300);
%SP = SP + 1;

toc;
fprintf( '=============== DONE ====================\n' );

%% Improve Disparity with Planes
if extract_plane_flag == 1
    
    %% Plane Estimation
    fprintf( '========== PLANE ESTIMATION ==================\n' );
    tic;

    PlaneHypos = Plane_Estimation ( Idis, theta, height, width, save_folder_disp, frame_number, SP, minTheta, maxTheta);

    toc;
    fprintf( '=============== DONE ====================\n' );

    %% Plane MRF Estimation
    fprintf( '========== PLANE MRF ESTIMATION ==================\n' );
    tic;
   
    config_MRF;
    opts = init();
    
    PlaneIdx = planeInference(SP, Idis, PlaneHypos, sprintf('%s/data/Prior/',opts.data_dir), paramsM, 0);
    
    
    Idis_MRF = showPlanes(SP, PlaneIdx, PlaneHypos);
   
    [x, y, z] = calc_point_from_disp_theta_phi(Idis_MRF, -pi, pi, 0, -pi/4, pi/4); 
    if show_results
       
        figure(3)
        imagesc(Idis_MRF);
        
    end
    if save_flag_mat 
        save( sprintf('%sIdis_MRF%06d.mat', save_folder_disp, frame_number), 'Idis_MRF');
    end
    
    Idis_MRF = disp_to_color (Idis_MRF, 0.6);
    imwrite( Idis_MRF, sprintf('%sIdis_MRF_%06d.png', save_folder_disp, frame_number ));
    
end

toc;
fprintf( '=============== DONE ====================\n' );

end
