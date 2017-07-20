#include "mex.h"
#include <math.h>
#include <iostream>

#define PI 3.141592654

typedef double (*pmatrix3)[3][3];

void spherical_rectification_coordinates (double* in, pmatrix3 T1, pmatrix3 T2, double* v2, double* v22) {
    
    double width        = in[0];
    double height       = in[1];
    double start_theta  = in[2];
    double end_theta    = in[3];
    double start_phi    = in[4];
    double end_phi      = in[5];
  
    int ind_phi = 1;
    int ind_theta = 1;
    int ind = 0;

    for ( int ind_theta = 1; ind_theta <= height; ind_theta++ ) {
        
        for ( int ind_phi = 1; ind_phi <= width; ind_phi++) {
    
            //double phi = (double)ind_phi * PI / width;
            double phi = ( start_phi +  (end_phi - start_phi) / width * (ind_phi-1) ) * PI / width;
           
            double theta = ( start_theta + (end_theta - start_theta) / height * (ind_theta-1) );
            
            //Sphere Coordinates 
            double v1x, v1y, v1z;
            v1x = sin(phi) * cos(theta);
            v1y = sin(phi) * sin(theta);
            v1z = cos(phi);
                        
            v2[0+3*ind] = (*T1)[0][0] * v1x + (*T1)[1][0] * v1y + (*T1)[2][0] * v1z;
            v2[1+3*ind] = (*T1)[0][1] * v1x + (*T1)[1][1] * v1y + (*T1)[2][1] * v1z;
            v2[2+3*ind] = (*T1)[0][2] * v1x + (*T1)[1][2] * v1y + (*T1)[2][2] * v1z;
                        
            v22[0+3*ind] = (*T2)[0][0] * v1x + (*T2)[1][0] * v1y + (*T2)[2][0] * v1z;
            v22[1+3*ind] = (*T2)[0][1] * v1x + (*T2)[1][1] * v1y + (*T2)[2][1] * v1z;
            v22[2+3*ind] = (*T2)[0][2] * v1x + (*T2)[1][2] * v1y + (*T2)[2][2] * v1z;
            
            ind = ind + 1;
         }
     }
}
           


void mexFunction (int nlhs,mxArray *plhs[],int nrhs,const mxArray *prhs[]) {
    
    // check arguments
    if (nrhs!=3)
      mexErrMsgTxt("6 inputs and required (p,vp,param).");
    if (!mxIsDouble(prhs[0]) || mxGetM(prhs[0])!=6)
      mexErrMsgTxt("Input must be a double 3xN matrix.");

    // get pointer to data
    double* in  = (double*)mxGetPr(prhs[0]);
    pmatrix3 T1 = (pmatrix3)mxGetPr(prhs[1]);
    pmatrix3 T2 = (pmatrix3)mxGetPr(prhs[2]);
    
	// allocate output memory
    int num = in[0]*in[1];
    const int dims[] = {3,num};
    plhs[0] = mxCreateNumericArray(2,dims,mxDOUBLE_CLASS,mxREAL);
    plhs[1] = mxCreateNumericArray(2,dims,mxDOUBLE_CLASS,mxREAL);
    
    double* out1 = (double*)mxGetPr(plhs[0]);
    double* out2 = (double*)mxGetPr(plhs[1]);

    spherical_rectification_coordinates (in, T1, T2, out1, out2);
}
