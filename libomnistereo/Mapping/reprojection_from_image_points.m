%% Minimize Reprojection Error
% input:    
%   - S             = all 3D points
%   - corners       = all image points
%   - points        = selected points for minimization
%   - param         = calibration
%   - calib_method  = calibration method
%                       published only  for method 14
%   - cams          = Camera or Cameras in which the error is minimized (Const or Vector)
%   - options       = Minimization Options
%   - motion_flag   = 1 - optimize motion / 0 - no motion optimization 
%   - point_flag    = 1 - optimize 3D points / 0 - no 3D point optimization
%%

function [x0, resnorm, residual] = reprojection_from_image_points ( S, corners, points, param, calib_method, cams, options, motion_flag, point_flag)

if motion_flag == 1 && point_flag == 0
    x0 = zeros( 6, size(points,1));
    resnorm = zeros( 6, size(points,1));
elseif motion_flag == 0 && point_flag == 1
	x0 = zeros( size(points,2)*3, size(points,1));
    resnorm = zeros( size(points,2)*3, size(points,1));
elseif motion_flag == 1 && point_flag == 1
    x0 = zeros( size(points,2)*3+6, size(points,1));
    resnorm = zeros( size(points,2)*3+6, size(points,1));
end

for num = 1 : size(points,1)
    
    u_ini = []; % Image points for optimized points
    for c = cams;
        for j = points(num,:)
            u_ini = [ u_ini; corners{1,c}.p(j,1); corners{1,c}.p(j,2)];
        end    
    end  

    % Optimization without 3D points
    if motion_flag == 1 && point_flag == 0
        
        xx = [0;0;0;0;0;0];
    
    elseif point_flag == 1
        
        xx = S(:,points(num,:));
        xx = reshape(xx,numel(xx),1);  

        if motion_flag == 0 
            xx = xx;
        elseif motion_flag == 1 
            % initial values for the 3D point and the motion between 1 and 3
            xx = [xx; 0; 0; 0; 0; 0; 0];
        end
    end
    
    % optimization
    [x0(:,num), resnorm(:,num), residual] = lsqnonlin( @min_func_reprojection, ...
        xx, -inf, inf, options, param, points(num,:), u_ini, S, calib_method, cams, motion_flag, point_flag);
    
end