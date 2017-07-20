% Reprojection function: map 3D point to a 2D point
% Input: 
%   - param: calibration parameter
%   - X: 3D points
%   - method: calibration method
%   - cams: number or vector for which camera we compute the image points
% Output:
%   - 2D image points
%
% M. Schönbein 2014

function [u] = reprojection_centered ( param, X, cams)

u = zeros ( 1, 2*size(cams,2)*size(X,2));
corners = 0;

for c = cams 
    
	XR =rigid_motion(X,param.cam{c}.ex_om,param.cam{c}.ex_T); 
    
	ut = projection_centered_mex( XR, param.cam{c}.centered.vp, param.cam{c}.centered.param);
    utr = reshape(ut, 1, size(ut,2)*2);
            
    u(corners + 1 : corners + size(utr,2)) = utr;
    corners = corners + size(utr,2); 

end

