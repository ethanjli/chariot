function S = estimate_3D_point_cloud (distanz, flag_disp, disp2, Cloud, phi, point_num, theta, distance_max, T1, ...
    Hex, recti) 

disp = disp2;
disp = double(disp);
disp(disp==255)=0;

size_M = size(find(disp(Cloud,1+(phi.length*0.2) : 1 : phi.length-(phi.length*0.2) )>0),1);
vec_in = [ size(Cloud,2); point_num; theta.start; theta.end; theta.length; phi.length; distanz; flag_disp; size(disp,1); size_M; distance_max];
[Xm, S] = compute_3D_point_cloud_mex(vec_in, disp, T1, Hex(1:3,1:3),Cloud',recti(:,:,1),recti(:,:,2),recti(:,:,3)); 



