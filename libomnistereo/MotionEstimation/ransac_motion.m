%%% Ransac for Motion Estimation
%
% Input: Point Cloud of 6 points
% Output: number and inlier

function [max_in, index_in] = ransac_motion ( corners, S, param, samples, calib)

J = zeros(samples * 6,6);

options=optimset('Algorithm','levenberg-marquardt', 'Display','off',... 
                 'TolX',1e-2, 'TolFun',1e-2, ...
                 'DerivativeCheck','off', 'Diagnostics','off', ...
                 'Jacobian','off', ...%'ScaleProblem', 'Jacobian',...
                 'JacobPattern',J,...
                 'MaxFunEvals', 1000, ...
                 'MaxIter',100);

max_in = 0;         % initilization of maximum inliers
cams = [ 3,4 ];     % number of the cameras which are minimized

for i=1:samples
    
    % take 3 random points out of S
    points = randi(size(corners{1,1}.p,1),1,3);

    % if ransac optimize only the extrinsics not the 3D points
    motion_flag = 1;
    point_flag = 0;    

    x0 = reprojection_from_image_points ( S, corners, points, param, calib, cams, options, motion_flag, point_flag);
     
    om = x0(end-2:end)';
    T  = x0(end-5:end-3);
       
	inliers =0; ind_in = []; 
   
    param.cam{3}.ex_T = x0(end-5:end-3); 
	param.cam{3}.ex_om = x0(end-2:end)'; 
        
	Hex = [ rodrigues(param.cam{2}.ex_om), param.cam{2}.ex_T; 0 0 0 1];
    Hm = [ rodrigues(x0(end-2:end)), x0(end-5:end-3); 0 0 0 1];
        
    H = Hex * Hm;
    param.cam{4}.ex_om = rodrigues( H(1:3,1:3))';
    param.cam{4}.ex_T = H(1:3,4);
            
        u = reprojection_centered ( param, S, cams);
    
    err1 = sqrt ( ( u(1:2:size(S,2)*2)' - corners{1,3}.p(:,1) ).^2 + ( u(2:2:size(S,2)*2)' - corners{1,3}.p(:,2) ).^2 );
    err2 = sqrt ( ( u(size(S,2)*2+1:2:end)' - corners{1,4}.p(:,1) ).^2 + ( u(size(S,2)*2+2:2:end)' - corners{1,4}.p(:,2) ).^2 );
    err = (err1 + err2) ./ 2;
    
    [in,j]=find(err<10.5);
    inliers = size(j);
    ind_in = in; 
    
    if inliers >= max_in
        max_in = inliers;
        index_in = ind_in; 
    end      

end
