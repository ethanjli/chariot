#include <mex.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <iostream>
#include <math.h>

#include <opencv.hpp>
#include "mc_convert/mc_convert.h"

using namespace std;

// main function
void mexFunction (int nlhs,mxArray *plhs[],int nrhs,const mxArray *prhs[]) {
  
  // check for proper number of arguments
  if(nrhs!=1)
    mexErrMsgTxt("One input required (img_in).");
  if(nlhs!=1) 
    mexErrMsgTxt("One output required (img_out).");  

  // check for proper argument types and sizes
  if(!mxIsUint8(prhs[0]) || mxGetNumberOfDimensions(prhs[0])!=2)
    mexErrMsgTxt("Input img_in must be a uint8 image.");

  // read img_in
  CvMat* img_in = mxArr_to_new_CvMat(prhs[0]);    

  // smooth image
   CvMat* img_out; //(cv::Size(img_in->height,img_in->width),IPL_DEPTH_8U,1);
//   cvSmooth(img_in,img_out,CV_GAUSSIAN,3,3);

  // set img_out
  plhs[0] = CvMat_to_new_mxArr(img_out);

  // release memory | IMPORTANT MIRIAM :)
  // always release inputs, too (img_in)
//   cvReleaseImage(&img_in);
//   cvReleaseImage(&img_out);
}
