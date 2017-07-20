function [ recti1, recti2 ] = ...
    rectified_image ( Qu1, Qv1, Qu2, Qv2, cam1, cam2, frame1, frame2, img_folder, name, save_folder_recti, colored_rectified, ...
    save_name1, save_name2, inter, save_image )


if colored_rectified == 1
    im1 = im2double( ( imread ( sprintf('%s/%s/image_0%d/data/%010d.png', img_folder, name, cam1, frame1 ) ) ) ); 
    im2 = im2double( ( imread ( sprintf('%s/%s/image_0%d/data/%010d.png', img_folder, name, cam2, frame2 ) ) ) ); 
else
    im1 = im2double( rgb2gray ( imread ( sprintf('%s/%s/image_0%d/data/%010d.png', img_folder, name, cam1, frame1 ) ) ) ); 
    im2 = im2double( rgb2gray ( imread ( sprintf('%s/%s/image_0%d/data/%010d.png', img_folder, name, cam2, frame2 ) ) ) ); 
end

Qu1(isnan(Qu1)) = 0;
Qv1(isnan(Qv1)) = 0;
Qu2(isnan(Qu2)) = 0;
Qv2(isnan(Qv2)) = 0;

[U,V] = meshgrid(1:size(im1,2),1:size(im1,1));
if colored_rectified == 1
    recti1 = interp2_with_color ( U, V, im1, Qu1, Qv1, inter);
    recti2 = interp2_with_color ( U, V, im2, Qu2, Qv2, inter);
else
    recti1 = interp2(U, V, im1, Qu1, Qv1, inter);
    recti2 = interp2(U, V, im2, Qu2, Qv2, inter);
    
    recti1 = recti1(:,:)';
    recti2 = recti2(:,:)';    
end

recti1=max(min(recti1,1),0);
recti2=max(min(recti2,1),0);

if save_image 
    imwrite( recti1, sprintf('%s%s_%06d.png', save_folder_recti, save_name1, frame1 ) );
    imwrite( recti2, sprintf('%s%s_%06d.png', save_folder_recti, save_name2, frame1 ) );
    
    %% Achtung Originialbilder werden auch gespeichert!
    imwrite( im1, sprintf('%sOrig_%s_%06d.png', save_folder_recti, save_name1, frame1 ) );
    imwrite( im2, sprintf('%sOrig_%s_%06d.png', save_folder_recti, save_name2, frame1 ) );
end

end 
        