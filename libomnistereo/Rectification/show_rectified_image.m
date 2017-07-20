% Spherical Rectification for MotionStereo and Stereo

function [recti1, recti2, T1, distanz, Hex] = show_rectified_image ( frame_number, img_folder, name, calibration_path, save_folder, cam1, cam2, M1, save_folder_recti)

% parameters for the rectification
config_rectification;

%load(sprintf('%scalib_0014inv.mat',calibration_path));
    
if cam1 ~= cam2

    load (  sprintf('%scalib_%04dinv.mat',calibration_path, calib_stereo) );
    
    Hex = [ rodrigues(param.cam{1}.ex_om), param.cam{1}.ex_T; 0 0 0 1];
    % Extrinsics in the sphere coordinate system
    if calib_stereo == 14
        T_ex = param.cam{1}.centered.vp + param.cam{2}.ex_T - param.cam{2}.centered.vp;
    else
        T_ex = param.cam{2}.ex_T;
    end
    om_ex = param.cam{2}.ex_om;
    
    %if (exist( sprintf('%scalib_0014rec.mat',calibration_path),'file')) == 2
        %load (  sprintf('%scalib_0014rec.mat',calibration_path) );
    if ( exist( sprintf('%scalib_%04drec.mat', calibration_path, calib_stereo), 'file' )) == 2
        load (  sprintf('%scalib_%04drec.mat',calibration_path, calib_stereo) );
        T1 = param.cam{1}.centered.T1s;
    else
        [param, T1, ~] = compute_sphere_rectifiation_stereo_map ( param, thetaS, phiS, T_ex, om_ex, calib_stereo );
    end
    
    distanz = norm(param.cam{2}.ex_T);

    % Save and compute rectified Stereo Image       
    [ recti1, recti2 ] = rectified_image ( param.rectified_behind.Qu1, param.rectified_behind.Qv1, ...
        param.rectified_behind.Qu2, param.rectified_behind.Qv2, cam1, cam2, frame_number, frame_number, img_folder, ...
        name, save_folder_recti, colored_rectified, 'stereo_left', 'stereo_right', inter, save_image  );  
   
    
elseif cam1 == cam2
    
    load (  sprintf('%scalib_%04dinv.mat',calibration_path, calib_motion) );
    
    cam_image = cam1-1;
    phi = phiM;
    if cam1 == 2
        theta = thetaML;
    elseif cam1 == 3
        theta = thetaMR;
    end
    
    Hex = [ rodrigues(param.cam{cam1-1}.ex_om), param.cam{cam1-1}.ex_T./1000; 0 0 0 1];

    [rectified_map, T1, T2, distanz] = compute_sphere_rectifiation_motion_map ( param, cam_image, theta, phi, M1, calib_motion);

    % Save and compute rectified Stereo Image       
    [ recti1, recti2 ] = rectified_image ( rectified_map.Qu1, rectified_map.Qv1, rectified_map.Qu2, rectified_map.Qv2, ...
        cam1, cam2, frame_number, frame_number+1, img_folder, name, save_folder_recti, colored_rectified, ...
        sprintf('motion_cam%01d_1',cam_image) , sprintf('motion_cam%01d_2',cam_image), inter, save_image );
     
end
    
end
