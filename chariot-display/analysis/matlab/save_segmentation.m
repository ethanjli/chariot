function [] = saveSegmentation(seg_file)
    seg = load(seg_file);
    images = seg.images;
    mkdir('SegmentedImages')
    for i = 1:size(images,1)
	im = imread(images(i, :));
	W = seg.W((2*i-1):(2*i), :);
	f = plot_segmentation(im, W, seg.labels_objects);
	saveas(f, ['SegmentedImages', '/image', num2str(i), '.png']);
    end
end


function [f] = plot_segmentation(im, W, labels)
    f = figure('Visible', 'off');
    image(im);
    hold on;
    n_labels = squeeze(max(labels, [],2));

    %Due to some bizarre bug, I can't use n_labels as the input to jet()
    colors = jet();
    n_colors = size(colors, 1);
     
    for i = 1:n_labels
	p(i) = plot(W(1, labels == i), W(2, labels == i), '+');
	set(p(i), 'Color', colors(floor(n_colors/n_labels) * i, :));
    end
    legend('show');
end
