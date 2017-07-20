% Changed 10.10.14 M.Schoenbein                             
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Input:
%  - seq_name               % Sequenz Name
%  - sequenz                % Number of the Sequenz
    
% 

function M1 = MotionEstimationSeq ( sequenz, start_seq, end_seq, result_folder, calibration_path, name )
 
warning off;

opts = init();
root_dir = opts.root_dir;

config_MotionEstimation;
config_FeatureMatching;
                          

for cur_seq = start_seq : end_seq
    
    %%%%%%%%%%%%%%%%%%% Feature Matching %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    save_name_feature = sprintf( '%s/FeatureMatching/%s_%s_%s_%s', result_folder, fm.detector, fm.descriptor, fm.image1, fm.image2);
    mkdir(save_name_feature);

    save_feature = sprintf( '%s/Corners/%s', save_name_feature );
    mkdir ( save_feature );

    if exist( sprintf('%scorners_%06d.mat', save_feature, cur_seq), 'file' ) == 0

        feature_quad_matching_mex( cur_seq, fm.detector, fm.descriptor, fm.matchingtype, fm.folder, name, fm.image1, fm.image2, ...
        save_name_feature, fm.mask_folder );

        FeaturesSeq_From_txt ( save_feature, save_name_feature, cur_seq )

    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    filename = sprintf('%s/MotionEstimation/%s_%s_%s_%s', result_folder, fm.detector, fm.descriptor, fm.image1, fm.image2);
    save_complete = sprintf('%s/Method_%02d_%02d/', filename, me.calib_initial, me.calib ); 

    %% Load Calibration Files
    calibIni = load ( sprintf( '%s/calib_%04d.mat', calibration_path, me.calib_initial) );
    calibIni.param.cam{1,3} = calibIni.param.cam{1,1};
    calibIni.param.cam{1,4} = calibIni.param.cam{1,2};

    calib = load ( sprintf( '%s/calib_%04d.mat', calibration_path, me.calib) );
    calib.param.cam{1,3} = calib.param.cam{1,1};
    calib.param.cam{1,4} = calib.param.cam{1,2};

    %% Sequenz
    X(:,cur_seq+1) = [0;0;0];
    H_all = eye(4,4);
    index_in = [];

    mkdir(sprintf('%sFrames', save_complete));

    frame = cur_seq + 1; 

    clear corners corners2 S S2 inliers index_in; 

    fprintf(1,'Run calculation for %d\n', frame-1);
        
    % Load Features from C Code
    old = load(sprintf('%scorners_%06d.mat', save_feature, frame-1));

            corners = distibuted_corner_selction ( old.corners, calibIni.param.cam{1}.c(1), calibIni.param.cam{1}.c(2) );

    cornersOrg = corners;                                                   
        for j=1:4
            corners{j}.p = centered_map_observations(calib.param.cam{j}.centered,corners{j}.p')';
        end

    %% Calculate Initial 3D point by Triangulation 
        S  = compute_3D_worldpoint ( cornersOrg, calibIni.param, me.calib_initial );

    % Verbessern der 3D Punkt durch Minimierung in Stereo [1:size(corners{1}.p,1)]
    if me.estimation3D_on == 1                                              
        motion_flag = 0;
        point_flag = 1;
        Px = reprojection_from_image_points ( S, corners, [1:size(corners{1}.p,1)], calib.param, me.calib, ...
            [1:2], me.options, motion_flag, point_flag);
        S = reshape(Px,3,size(S,2));
    end                                                                     
 
    % compute Inlier
    [inliers, index_in] = ransac_motion ( corners, S, calib.param, nums_ran, me.calib); 


    
    % Motion Estimation with Inliers
    motion_flag = 1;
    point_flag = 0; 

    x0 = reprojection_from_image_points ( S, corners, index_in', calib.param, me.calib, [3,4], me.options, motion_flag, point_flag);
    M(:,frame) = x0(end-5:end);
    M1 =  x0(end-5:end);

	if me.saveEveryFrame_on == 1 
    	save(sprintf('%sFrames/M_%06d_ErrRan%03d.mat', save_complete, seq, nums_ran), 'M1', 'S', 'index_in');
    end 
                  
end

end

