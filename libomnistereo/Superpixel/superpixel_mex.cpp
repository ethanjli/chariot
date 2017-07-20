#include "mex.h"
#include "mexopencv.hpp"
#include <iostream>

#include <opencv/cv.h>
#include <opencv/highgui.h>
#include <tbb/tbb.h>
#include "mc_convert.h"

#include "SLICSuperpixel.h"

using namespace std;

void superpixel( Mat& img1, Mat& result, int number, int threshold) {
  
    /* Generate super pixels */
    std::cout << "Start" << std::endl;

    SLICSuperpixel slic( img1, number, threshold);
    slic.generateSuperPixels();
    
    result = slic.getClustersIndex();
    
    /* Draw the contours bordering the clusters */
    vector<Point2i> contours = slic.getContours();
    for( Point2i contour: contours )
        img1.at<Vec3b>( contour.y, contour.x ) = Vec3b(255, 0, 255);

}


void mexFunction (int nlhs, mxArray *plhs[],int nrhs,const mxArray *prhs[]) {
    
    // check arguments
    if (nrhs!=3)
      mexErrMsgTxt("1 inputs and required (image_1).");
     
    // Convert MxArray to cv::Mat and cv::Size
    cv::Mat img1 = MxArray(prhs[0]).toMat(), img_out;
    
    double* number  = (double*)mxGetPr(prhs[1]);
    double* threshold = (double*)mxGetPr(prhs[2]);
        
    superpixel( img1, img_out, *number, *threshold);
    
    // Convert cv::Mat back to mxArray*
    plhs[0] = MxArray(img_out);
    plhs[1] = MxArray(img1);
    
   
}