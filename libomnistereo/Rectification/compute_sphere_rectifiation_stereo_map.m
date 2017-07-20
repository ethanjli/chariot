function [param, T1, T2] = compute_sphere_rectifiation_stereo_map ( param, thetaB, phiB, T_ex, om_ex, calib_stereo )

% for stereo rectification different cameras
cam1 = 1;
cam2 = 2;

% compute fundamental matrix for stereo
F = compute_fundamental_matrix ( T_ex, om_ex);

% compute rectified map bebind the vehicle
R = rodrigues(om_ex);
[param.rectified_behind, T1, T2] = spherical_rectification ( param, F, R, phiB, thetaB, cam1, cam2, calib_stereo);

