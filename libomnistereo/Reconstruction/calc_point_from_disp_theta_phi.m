function [x, y, z] = calc_point_from_disp_theta_phi(disp, thetaMin, thetaMax, phiMin, phiMax)

% arguments:
% disp -- disparity image, right now considered approximately the inverse (scaling can be added later)
% theta -- horizontal angle (across width of image)
% phi -- vertical angle 

% outputs:
% x,y,z -- x points right, y points toward the screen, z is upward


depth = 1 ./ disp;

depth_width = size(depth, 2);
depth_height = size(depth, 1);

theta = 1 : depth_width;
theta = repmat (theta, depth_height, 1);
theta = (thetaMax - thetaMin)/depth_width * theta  - thetaMin;

phi =  1 : depth_height;
phi = repmat (phi, depth_width, 1)';
phi = (phiMax - phiMin)/depth_height * phi  - phiMin;


%calculate x, y, z
z = depth .* sin(phi);
x = depth .* sin(theta) .* cos(phi);
y = depth .* cos(theta) .* cos(phi);


