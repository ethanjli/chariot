% Conversion in the 360° Disparity Image from phi to phi_discret
% Input: 
% - phi - Angle in degree
% - height - image size
% Output:
% - phiD - dircret angle phi

function [phi_dis, theta_dis] = conversion_360disp_angle2angleD ( phi, height, theta, width, minTheta, maxTheta)

phi_dis = round ( ( phi + pi) / (2*pi) * (height-1)); 

theta_dis = round(( ( theta - minTheta ) / ( maxTheta - minTheta )) * (width-1));