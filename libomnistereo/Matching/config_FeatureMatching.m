%% conifg_feature matching
%% Parameter for feature matching
opts = init();

fm.detector = 'FAST';
fm.descriptor = 'BRIEF';
fm.matchingtype = 'Hamming';

fm.image1 = 'image_02';
fm.image2 = 'image_03';
fm.folder = opts.img_folder;
fm.mask_folder = sprintf('%s/data/Masks/',opts.data_dir);
