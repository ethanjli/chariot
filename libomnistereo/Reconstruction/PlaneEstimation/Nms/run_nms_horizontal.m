function maximaH = run_nms_horizontal ( H, folder, frame_number, threshold, sigma, n, debug_flag, save_debug_flag)

HT = imfilter(H,fspecial('gaussian',sigma*[3,3],sigma),'replicate');
maximaH = nonMaximumSuppression(HT,n,threshold,0);

if (debug_flag)
    figure,plot(HT);hold on;
    plot(maximaH(:,1),maximaH(:,2),'xr','MarkerSize',10,'LineWidth',2);
end

maximaH(:,1) = maximaH(:,1);

if save_debug_flag 
    save ( sprintf('%smaximaH_%03d.mat', folder, threshold), 'maximaH');
end