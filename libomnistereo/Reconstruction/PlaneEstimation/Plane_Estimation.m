function PlaneHypos = Plane_Estimation ( Idis, theta, height, width, save_folder_disp, frame_number, SP, minTheta, maxTheta )

config_PlaneEstimation;

%% compute Plane Probability
if exist ( sprintf('%s/P_hor_%06d.mat', save_folder_disp, frame_number))~= 2
    load('glm.mat','glm');
    Idis_var = computeDisparityVariance(Idis);
    P_hor = computeHorizontalPlaneProbability(Idis_var,glm);
    save ( sprintf('%s/P_hor_%06d.mat', save_folder_disp, frame_number), 'P_hor');
else
    load ( sprintf('%s/P_hor_%06d.mat', save_folder_disp, frame_number), 'P_hor');
end

%% compute horizontal maxima
HT = plane_hough_horizontal ( Idis, P_hor, save_folder_disp, width, d_scale_hori, index, HT, minTheta, maxTheta, debug_flag, save_debug_flag);
maxima_horizontal = run_nms_horizontal ( HT, save_folder_disp, frame_number, threshold_hori, sigma_hori, n, debug_flag, save_debug_flag);

z_hypo = [ - (maxima_horizontal(:,1)-1)./d_scale_hori, - ones(size(maxima_horizontal,1),1)] ;

%% run Hough Planes
H = plane_hough ( Idis, P_hor, save_folder_disp, frame_number, height, max_dist, d_scale, index, H, debug_flag, save_debug_flag);

% Save Results for different NonMaximaSuppression Results for vertical planes
for k = 1 : length(threshold_nms)

    %% Run NumMaximaSupression
    maxima = run_nms_vertical ( H, save_folder_disp, frame_number, threshold_nms(k), sigma_vertical, debug_flag, save_debug_flag);

    if isempty(maxima)~=1
        [alpha, d] = vertical_hypothese_plane ( maxima(:,1), h, maxima(:,2), d_scale);
        v_hypo = [alpha, d];
    else
        v_hypo = [];
    end

    %% Hypothese
    PlaneHypos = [v_hypo; z_hypo ];

    if save_debug_flag
        % save maxima
        save( sprintf('%sPlaneHypos_%03d.mat', save_folder_disp, threshold_nms(k)), 'PlaneHypos');
    end
    
    %% compute the R Matrix for all Superpixel and Plane Hypothese
    [PlaneDist, PlaneIndexWTA] = plane_hypothese ( SP, Idis, height, width, minTheta, maxTheta, PlaneHypos );

    if save_debug_flag
        save( sprintf('%sPlaneDist_%03d.mat', save_folder_disp, threshold_nms(k)), 'PlaneDist');
        save( sprintf('%sPlaneIndexWTA_%03d.mat', save_folder_disp, threshold_nms(k)), 'PlaneIndexWTA');
    end

    if show_WTA_result
        Inew  = showPlanes( SP, PlaneIndexWTA, PlaneHypos);

        Inew = disp_to_color (Inew, 0.6);
        imwrite( Inew, sprintf('%sImgWTA_%03d.png', save_folder_disp, threshold_nms(k) ));
    end
end

end