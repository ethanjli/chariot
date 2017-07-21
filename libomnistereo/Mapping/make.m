opts = init;

if (isunix == 1)
    mex('rodriguesMex.cpp',['-Wl,-rpath,', opts.sys_lib_dir],['-L',opts.opencv_lib_dir], '-lopencv_core', '-lopencv_imgproc', '-lopencv_highgui', '-lopencv_features2d', '-lopencv_calib3d')
else
    mex('rodriguesMex.cpp',['-I"',opts.opencv_inc_dir,'"'],['-L"',opts.opencv_lib_dir,'"'], ...
    ['-lopencv_core', opts.opencv_version], ['-lopencv_imgproc', opts.opencv_version], ...
    ['-lopencv_highgui', opts.opencv_version], ['-lopencv_features2d', opts.opencv_version], ['-lopencv_calib3d', opts.opencv_version])
end

disp('Done RodriguesMapping!');
 
