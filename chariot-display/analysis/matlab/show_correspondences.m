function H = show_correspondences(seg_file)
    clc;
    
    seg = load(seg_file);
    
    n_labels = max(seg.labels_objects, [], 2);
    n_images = size(seg.images, 1);

    for i = 0:n_labels
	new_folder = ['label', int2str(i)];
	mkdir(new_folder);	

	for j = 1:n_images-1
		single_correspondence(seg, j, j+1, i, new_folder);
	end
    end

end

function H = single_correspondence(seg, i1, i2, label, new_folder)
    im1 = imread(seg.images(i1, :));
    im2 = imread(seg.images(i2, :));
    mask = seg.Z(i1, :) & seg.Z(i2, :);
    
    if label < 1 
	    w1 = seg.W(2*i1-1 : 2*i1,  mask)';
	    w2 = seg.W(2*i2-1 : 2*i2,  mask)';
    else
	    w1 = seg.W(2*i1-1 : 2*i1, seg.labels_objects == label & mask)';
	    w2 = seg.W(2*i2-1 : 2*i2, seg.labels_objects == label & mask)';
    end

    figure('Visible', 'off'); ax = axes;
    H = save_matched_features(im1, im2, w1, w2, 'falsecolor');
    saveas(gcf, [new_folder, '/match', int2str(i1), int2str(i2),'.png']);

end
