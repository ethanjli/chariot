function opts = init()
% returns root_dir, adds path if no output specified

opts.root_dir = '/home/ageiger/omni_stereo';

% Image Folder (Test Data Folder)
opts.img_folder = sprintf('%s/data/Test_Sequenz/',opts.root_dir);
%		NOTE: images must be sorted in the way of the testsequence
%		(Eg. <img_folder>/2013_05_14_drive_0008_sync/image_02/data)

opts.opencv_lib_dir = '/usr/local/lib';
opts.opencv_inc_dir = '/usr/local/include/opencv2';
opts.opencv_version = '';
opts.tbb_inc_dir = '/usr/include';

% only applied once at the beginning
if nargout==0
  %mkdir(opts.filename);   
  addpath(genpath(sprintf('%s/src',opts.root_dir)));
end 