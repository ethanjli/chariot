% Conversion in the 360° Disparity Image from phi to phi_discret
% Input: 
% - phi - Angle in degree
% - height - image size
% Output:
% - phiD - dircret angle phi

function phi = conversion_360disp_phiD2phi ( phiD, height)

phi = (phiD ./ (height-1) * (2*pi)) - pi;