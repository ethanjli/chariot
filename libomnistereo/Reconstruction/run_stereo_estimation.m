function S = run_stereo_estimation ( frame_number, img_folder, name, calibration_path, save_folder, cam1, cam2, M1)

config_rectification;

save_folder_recti = sprintf('%s/Rectification/', save_folder);
mkdir(save_folder_recti);

[recti1, recti2, T1, distanz, Hex] = show_rectified_image ( frame_number, img_folder, name, calibration_path, save_folder, cam1, cam2, M1, ...
    save_folder_recti);

if cam1 ~= cam2
    size_recti_1 = thetaS.length;
    size_recti_2 = phiS.length + 300;
    savename = 'stereo';
else
    size_recti_1 = thetaMR.length;
    size_recti_2 = phiM.length + 300;
    if cam1 == 2
        savename = 'motion_left';
    else
        savename = 'motion_right';
    end
end

recti11(:,:,1) = zeros(size_recti_1,size_recti_2);
recti11(:,:,2) = zeros(size_recti_1,size_recti_2);
recti11(:,:,3) = zeros(size_recti_1,size_recti_2);
recti11(:,301:end,:) = recti1;

recti22(:,:,1) = zeros(size_recti_1,size_recti_2);
recti22(:,:,2) = zeros(size_recti_1,size_recti_2);
recti22(:,:,3) = zeros(size_recti_1,size_recti_2);
recti22(:,301:end,:) = recti2;

if (cam1 ~= cam2) && calib_stereo == 14
    
    disp2 = zeros(size(recti1,1),size(recti1,2));

    disp = sgbm_mex ( uint8(rgb2gray(recti22(1:border1,:,:)).*255), uint8(rgb2gray(recti11(1:border1,:,:)).*255));
    disp22 = double( disp) ./ 16;
    disp2(1:border1,:)= disp22(:,301:end,:);
    disp2(1:border1,:) = disp2(1:border1,:) .* double(maske_stereo(1:border1,:)./255);
 
    disp = sgbm_mex ( uint8(rgb2gray(recti22(border2:end,:,:)).*255), uint8(rgb2gray(recti11(border2:end,:,:)).*255));
    disp22 = double( disp) ./ 16;
    disp2(border2:end,:)= disp22(:,301:end,:);
    disp2(border2:end,:) = disp2(border2:end,:) .* double(maske_stereo(border2:end,:)./255);

else    

    disp = sgbm_mex ( uint8(rgb2gray(recti22).*255), uint8(rgb2gray(recti11).*255) );
	dispT2 = double( disp) ./ 16;
    disp2 = dispT2(:,301:end,:);
    
end

disp2(disp2==-1) = 255;
disp2(disp2==0) = 255;
disp_color = disp_to_color(disp2 ./max(max(disp2 )), 0.6); 
          

if save_image 
    %imwrite( disp2./max(max(disp2)), sprintf('%s%s_%s_%06d.png', save_folder_recti, savename, savename_image, frame_number ) ); % + (frame-1)));
    imwrite( disp_color,  sprintf('%s%s_%s_color_%06d.png', save_folder_recti, savename, savename_image, frame_number ) );
end


% compute 3D POint Cloud
if estimate_point_cloud == 1

    flag_disp = 2;      % flag_disp == 1 ( positive disparity) flag_disp == 2 (negative disparity)
    
    if cam1 ~= cam2
        Cloud       = StereoCloud;
        phi         = phiS;
        theta       = thetaS;
    elseif cam1 == 2
        Cloud       = LeftCloud;
        phi         = phiM;
        theta       = thetaML;
    elseif cam1 == 3
        Cloud       = RightCloud;
        phi         = phiM;
        theta       = thetaMR;
    end

    S = estimate_3D_point_cloud (distanz, flag_disp, disp2, Cloud, phi, point_num, theta, distance_max, T1, ...
                Hex, recti2);
            
	if save_point_cloud
        show_3D_point_cloud ( S );
    end

    if save_point_cloud_mat
        save( sprintf('%s%s_%s_%06d.mat', save_folder_recti, savename_pointcloud, savename, frame_number ), 'S'); 
    end
            
end
