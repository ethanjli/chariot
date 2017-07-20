function R = roadPlaneToCamera(plane)

% r2 (facing bottom) = normal vector
r2 = (plane/norm(plane))';

% r1 (facing right) is defined by the following constraints:
% - x=0
% - r2'*r1=0
% - norm(r1)=1
r1y = -sqrt(r2(3)*r2(3)/(r2(3)*r2(3)+r2(2)*r2(2))); % neg => to the right
r1z = -r2(2)*r1y/r2(3);
r1  = [0;r1y;r1z];

% r3 (facing forward) is the cross product
r3 = cross(r1,r2);
if r3(1)<0
  r3 = -r3;
end

% put rotation matrix together
R = [r3 -r1 -r2];
