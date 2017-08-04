function opts = init()
% returns root_dir, adds path if no output specified

opts.root_dir = '/home/tj/Repositories/chariot/libomnistereo';
opts.data_dir = '/home/tj/Data/Geiger';

% Image Folder (Test Data Folder)
opts.img_folder = '/home/tj/Data/Geiger';

opts.sys_lib_dir = '/usr/lib/x86_64-linux-gnu';
opts.opencv_lib_dir = '/usr/lib/x86_64-linux-gnu';
opts.opencv_inc_dir = '/usr/include/opencv2';
opts.opencv_version = '';
opts.tbb_inc_dir = '/usr/include';

% only applied once at the beginning
if nargout==0
  %mkdir(opts.filename);   
  addpath(genpath(opts.root_dir));
end 
