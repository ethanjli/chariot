function [f] = find_features(im_file, num_strongest)
    im = rgb2gray(imread(im_file));
    
    points = detectSURFFeatures(im);
    [dud, points] = extractFeatures(im, points);
    
    f = figure('Visible', 'off');
    imagesc(im);
    hold on;
    plot(points.selectStrongest(num_strongest));
    
    [path, name, ext] = fileparts(im_file);
    ext='png';
    saveas(f, [name  '_features.' ext], ext);
end

