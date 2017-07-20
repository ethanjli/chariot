%mex feature_quad_matching_mex.cpp MatchingQuadSmall.cpp -lopencv_core -lopencv_imgproc -lopencv_highgui -lopencv_ml -lopencv_features2d -lopencv_calib3d -lopencv_objdetect -lopencv_contrib -lopencv_legacy -lopencv_flann -lopencv_video -lopencv_nonfree
opts = init;

if (isunix == 1)
    mex('feature_quad_matching_mex.cpp', 'MatchingQuadSmall.cpp',['-L',opts.opencv_lib_dir], '-lopencv_core', '-lopencv_imgproc', '-lopencv_highgui', '-lopencv_features2d', '-lopencv_calib3d', '-lopencv_nonfree')
else
    mex('feature_quad_matching_mex.cpp', 'MatchingQuadSmall.cpp',['-I"',opts.opencv_inc_dir,'"'],['-L"',opts.opencv_lib_dir,'"'], ...
    ['-lopencv_core', opts.opencv_version], ['-lopencv_imgproc', opts.opencv_version], ...
    ['-lopencv_highgui', opts.opencv_version], ['-lopencv_features2d', opts.opencv_version], ['-lopencv_calib3d', opts.opencv_version], ['-lopencv_nonfree', opts.opencv_version])
end


disp('Done QuadMatching!');