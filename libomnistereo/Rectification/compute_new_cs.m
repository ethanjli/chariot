function [T1, T2] = compute_new_cs (F, R, coord)

[u d v] = svd(F);
epi21 = [ u(:,end)];
epi22 = [-u(:,end)];
epi11 = [ v(:,end)];
epi12 = [-v(:,end)];

epi11 = epi11 / norm(epi11);
epi12 = epi12 / norm(epi12);
epi21 = epi21 / norm(epi21);
epi22 = epi22 / norm(epi22);

[C,I] = max(abs(epi11));
if epi11(I) >= 0
    epi = epi11;
    epi11 = epi12;
    epi12 = epi;
end

[C,I] = max(abs(epi21));
if epi21(I) >= 0
    epi = epi21;
    epi21 = epi22;
    epi22 = epi;
end

%coordinate system for the 1. image
if coord == 1
    up1 = [0;1;0];
elseif coord == 2
	up1 = [1;0;0];
end
    
%view = epi11;
r3 = epi11;
r2 = up1-(epi11'*up1)*epi11;
r1 = cross(r2,r3);


T1(:, 1) = r1/norm(r1);
T1(:, 2) = r2/norm(r2);
T1(:, 3) = r3/norm(r3);

T2 = R * T1;

end

