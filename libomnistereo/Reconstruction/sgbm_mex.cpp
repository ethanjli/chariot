#include "mex.h"
#include <iostream>
#include <opencv2/highgui/highgui.hpp>
#include "opencv2/calib3d/calib3d.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/contrib/contrib.hpp"
#include "opencv.hpp"
#include "mc_convert.h"
#include <math.h>

using namespace cv;

void sgbm_mex ( Mat img1, Mat img2, Mat disp, int alg) {
    
const char* disparity_filename = 0;

int SADWindowSize = 0, numberOfDisparities = 0;
bool no_display = true;
float scale = 1.f;

StereoBM bm;
StereoSGBM sgbm;

Size img_size = img1.size();

Rect roi1, roi2;
Mat Q;

bm.state->preFilterCap = 31;
bm.state->SADWindowSize = SADWindowSize > 0 ? SADWindowSize : 11;
bm.state->minDisparity = 0;
//bm.state->numberOfDisparities = numberOfDisparities > 0 ? numberOfDisparities : img_size.width/8;
bm.state->numberOfDisparities = 64;
//bm.state->textureThreshold = 10;
//bm.state->uniquenessRatio = 15;
bm.state->speckleWindowSize = 50;
bm.state->speckleRange = 32;

numberOfDisparities = numberOfDisparities > 0 ? numberOfDisparities : ((img_size.width/8) + 15) & -16;
sgbm.numberOfDisparities = 256; //64;

sgbm.preFilterCap = 63; //63; //63;
sgbm.SADWindowSize = 5; //5; //SADWindowSize > 0 ? SADWindowSize : 3;

int cn = img1.channels();

sgbm.P1 = 8*cn*sgbm.SADWindowSize*sgbm.SADWindowSize; // 
sgbm.P2 = 32*cn*sgbm.SADWindowSize*sgbm.SADWindowSize; // 
sgbm.minDisparity = 0;
//sgbm.uniquenessRatio = 10; // sgbm.uniquenessRatio = 1;
sgbm.speckleWindowSize = 50; // sgbm.speckleWindowSize = bm.state->speckleWindowSize;
sgbm.speckleRange = 32; // sgbm.speckleRange = bm.state->speckleRange;
sgbm.disp12MaxDiff = 10; //10; //3;
sgbm.fullDP = true;
// sgbm.P1 = 1200;
// sgbm.P2 = 2400;

Mat disp8;

int64 t = getTickCount();

if ( alg == 1 ) {
    std::cout << "Block Matching" << std::endl;
	bm(img1, img2, disp);
} else {
    sgbm(img1, img2, disp);
}

t = getTickCount() - t;
printf("Time elapsed: %fms\n", t*1000/getTickFrequency());

normalize(disp, disp8, 0, 255, CV_MINMAX, CV_8U);

}


void mexFunction (int nlhs, mxArray *plhs[],int nrhs,const mxArray *prhs[]) {
    
    // check arguments
    if (nrhs!=2)
      mexErrMsgTxt("6 inputs and required (image_1, image_2, detector, descriptor, matching, threshold).");
//     if (!mxIsDouble(prhs[0]) || mxGetM(prhs[0])!=2)
//       mexErrMsgTxt("Input must be a double 6x1 matrix.");
    
    // read img_in
    CvMat* img1 = mxArr_to_new_CvMat(prhs[0]);  
    CvMat* img2 = mxArr_to_new_CvMat(prhs[1]); 

    int alg = 0;
    
    // init additional data
    CvSize im_size = cvGetSize(img1);
    CvMat* img_out = cvCreateMat(im_size.height,im_size.width, CV_16S);
    
    sgbm_mex( img1, img2, img_out, alg);
        
    plhs[0] = CvMat_to_new_mxArr(img_out);

    
    cvReleaseMat(&img1);
    cvReleaseMat(&img_out);
              
}