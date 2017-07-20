% Spherical Rectification for MotionStereo and Stereo
% Output
%  - Rectified Map

function [rectified, T1, T2] = spherical_rectification ( param, F, R, phiValue, thetaValue, cam1, cam2, calib)

    start_theta = thetaValue.start;
    end_theta = thetaValue.end;
    height = thetaValue.length;

    start_phi = phiValue.start;
    end_phi = phiValue.end;
    width = phiValue.length;
        
    if cam1 == cam2
        coord = 2;
    else 
        coord = 1;
    end

    [T1, T2] = compute_new_cs (F, R, coord);

    [v2, v22] = spherical_rectification_coordinates_mex ( [width; height; start_theta; end_theta; start_phi; end_phi], T1, T2); 

        % new 3D point in the centered omni image        
        z2 = projection_centered_mex( v2*1000, param.cam{cam1}.centered.vp, param.cam{cam1}.centered.param);
        z22 = projection_centered_mex( v22*1000, param.cam{cam2}.centered.vp, param.cam{cam2}.centered.param);

        t2 = inverse_centered_map_observations(param.cam{cam1}.centered, z2)';
        t22 = inverse_centered_map_observations(param.cam{cam2}.centered, z22)';
    

    rectified.Qu1 = reshape(t2(:,1),width,height);
    rectified.Qv1 = reshape(t2(:,2),width,height);
    rectified.Qu2 = reshape(t22(:,1),width,height);
    rectified.Qv2 = reshape(t22(:,2),width,height);

end


