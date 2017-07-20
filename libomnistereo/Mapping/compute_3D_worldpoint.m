% compute 3d world point
function S = compute_3D_worldpoint ( corners, param, calib)

        [Xmir, vr] = inverse_projection_mirror ( corners, param);

    for i = 1 : size(Xmir,2)
        Xmir(:,i,2) = rodrigues(param.cam{2}.ex_om)' * [ Xmir(:,i,2) - param.cam{2}.ex_T];
        vr(:,i,2)   = rodrigues(param.cam{2}.ex_om)' * vr(:,i,2) ;
    end

    S = triangulation_3d_point ( Xmir, vr);
