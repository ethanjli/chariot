function maximaV = run_nms_vertical ( H, folder, frame_number, threshold, sigma, debug_flag, save_debug_flag)

H2 = imfilter(H,fspecial('gaussian',sigma*[3,3],sigma),'replicate');
H3 = zeros(size(H2,1)+20,size(H2,2)+20);
H3(11:end-10,11:end-10) = H2;

maximaV = nonMaximumSuppression(H3,3,threshold,0);

if (debug_flag)
    figure,imagesc(H3); axis equal; hold on; 
    colormap gray; 
    plot(maximaV(:,1),maximaV(:,2),'xr');
end

if isempty(maximaV)~=1
    maximaV(:,1) = maximaV(:,1)-10;
    maximaV(:,2) = maximaV(:,2)-10;
end

if save_debug_flag
    save ( sprintf('%smaximaV_%03d.mat', folder, threshold), 'maximaV');
end