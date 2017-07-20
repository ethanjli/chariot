function [rectified_left, T1, T2, distanz] = compute_sphere_rectifiation_motion_map ( param, cam, thetaB, phiB, M1, calib_motion)


if cam == 1
    
        T = param.cam{1}.centered.vp + M1(1:3) - param.cam{2}.centered.vp;
    om = M1(4:6)';
    R = rodrigues(om);
    
elseif cam == 2
    
    T = param.cam{1}.centered.vp + M1(1:3) - param.cam{2}.centered.vp;
    Hex = [ rodrigues(param.cam{2}.ex_om), param.cam{2}.ex_T; 0 0 0 1];
    Hm = [ rodrigues(M1(4:6)'), T; 0 0 0 1];
    
    H = (Hex) * Hm * inv(Hex);
    T = H(1:3,4);
    R = H(1:3,1:3);
    
end

F = [ 0, -T(3), T(2); T(3), 0, -T(1); -T(2), T(1),0] * R;

distanz = norm(T);

% compute rectified map bebind the vehicle
    [rectified_left, T1, T2] = spherical_rectification ( param, F, R, phiB, thetaB, cam, cam, calib_motion);
