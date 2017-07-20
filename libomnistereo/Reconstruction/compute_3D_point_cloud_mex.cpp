#include "mex.h"
#include <math.h>
#include <iostream>

#define PI 3.141592654

typedef double (*pmatrix3)[3][3];

 void compute_3D_point_cloud (double* disp, double* in, double* Xm, double* Xm_sel, pmatrix3 T1, pmatrix3 Hex, double* cloud, double* I1, double* I2, double* I3) {
  
    double CloudSize        = in[0];
    double point_num        = in[1];
    double thetaB_start     = in[2];
    double thetaB_end       = in[3];
    double thetaB_length    = in[4];
    double phiB_length      = in[5];
    double d                = in[6];
    double flag             = in[7];
    int sizeI            = in[8];
    int border           = in[10];
    
    double Xs1x,Xs1y,Xs1z;
    double XsRx, XsRy, XsRz;
    
    int ind = 0;
    int ind_sel = 0;
    
    double alpha, phi1;
    int i;
    
    for (int n = 0; n < CloudSize; n++) {
        i = cloud[n];
        
        for (int j = 1+(phiB_length*0.2); j <= phiB_length-(phiB_length*0.2); j++) {

            if (disp[(j-1)*sizeI+i-1] > 0) {
            
                //gamma = Disparität   
                double gamma = disp[(j-1)*sizeI+i-1] * PI / phiB_length; 
                double theta1 = ( thetaB_start + (thetaB_end - thetaB_start) / thetaB_length * (i-1) );
                
                
                if (flag == 1) {// Bilder nicht vertauscht

                    phi1 = j * PI / phiB_length;

                    alpha = gamma + phi1;

                } else if (flag == 2) { //% Bilder sind vertauscht

                    alpha = j * PI / phiB_length;

                    phi1 = alpha - gamma;

                }

                //compute R1
                double R1 = d * sin(alpha) / sin(gamma);
                             
                //compute 3D point in the sphere coordinate system
                Xs1x = sin(phi1) * cos(theta1);
                Xs1y = sin(phi1) * sin(theta1);
                Xs1z = cos(phi1);
                  
                 XsRx = R1/1000 *Xs1x;
                 XsRy = R1/1000 *Xs1y;
                 XsRz = R1/1000 *Xs1z;

                 double v2x, v2y, v2z;
                      
                 v2x = (*T1)[0][0] * XsRx + (*T1)[1][0] * XsRy + (*T1)[2][0] * XsRz;
                 v2y = (*T1)[0][1] * XsRx + (*T1)[1][1] * XsRy + (*T1)[2][1] * XsRz;
                 v2z = (*T1)[0][2] * XsRx + (*T1)[1][2] * XsRy + (*T1)[2][2] * XsRz;

                 Xm[0+5*ind] = (*Hex)[0][0] * v2x + (*Hex)[0][1] * v2y + (*Hex)[0][2] * v2z;
                 Xm[1+5*ind] = (*Hex)[1][0] * v2x + (*Hex)[1][1] * v2y + (*Hex)[1][2] * v2z;
                 Xm[2+5*ind] = (*Hex)[2][0] * v2x + (*Hex)[2][1] * v2y + (*Hex)[2][2] * v2z;
                 
                 Xm[3+5*ind] = (double)i;
                 Xm[4+5*ind] = (double)j;
                 
                 if ( (abs(Xm[0+5*ind]) <= border) && (abs(Xm[1+5*ind]) <= border) && (abs(Xm[2+5*ind]) <= border)) {
 
                     Xm_sel[0+6*ind_sel]= Xm[0+5*ind];
                     Xm_sel[1+6*ind_sel]= Xm[1+5*ind];
                     Xm_sel[2+6*ind_sel]= Xm[2+5*ind];
                    
                     if ((I1[(j-1)*sizeI+i-1] >= 0) && (I1[(j-1)*sizeI+i-1] <= 1)) {
                         Xm_sel[3+6*ind_sel] =I1[(j-1)*sizeI+i-1];
                         Xm_sel[4+6*ind_sel] =I2[(j-1)*sizeI+i-1];
                         Xm_sel[5+6*ind_sel] =I3[(j-1)*sizeI+i-1];
                          
                     } else {
                         Xm_sel[3+6*ind_sel] = 1;
                         Xm_sel[4+6*ind_sel] = 1;
                         Xm_sel[5+6*ind_sel] = 1;
                     }
 
                    ind_sel = ind_sel + 1;
                 }
                 
                 ind = ind + 1;
            }       
        }
    }
}

    
void mexFunction (int nlhs,mxArray *plhs[],int nrhs,const mxArray *prhs[]) {
    
    // check arguments
    if (nrhs!=8)
      mexErrMsgTxt("8 inputs and required (p,vp,param).");
//    if (!mxIsDouble(prhs[0]) || mxGetM(prhs[0])!=4)
//      mexErrMsgTxt("Input must be a double 3xN matrix.");

    
    // get pointer to data
    double* in  = (double*)mxGetPr(prhs[0]);
    pmatrix3 T1 = (pmatrix3)mxGetPr(prhs[2]);
    pmatrix3 Hex = (pmatrix3)mxGetPr(prhs[3]);
    double* disp = (double*)mxGetPr(prhs[1]);
    double* cloud = (double*)mxGetPr(prhs[4]);
	double* I1 = (double*)mxGetPr(prhs[5]);
    double* I2 = (double*)mxGetPr(prhs[6]);
    double* I3 = (double*)mxGetPr(prhs[7]);

    int num = in[9];
    const int dims1[] = {5,num};
    const int dims2[] = {6,num};
    plhs[0] = mxCreateNumericArray(2,dims1,mxDOUBLE_CLASS,mxREAL);
    plhs[1] = mxCreateNumericArray(2,dims2,mxDOUBLE_CLASS,mxREAL);
     
     double* Xm = (double*)mxGetPr(plhs[0]);
     double* Xm_sel = (double*)mxGetPr(plhs[1]);

     compute_3D_point_cloud (disp, in, Xm, Xm_sel, T1, Hex, cloud, I1, I2, I3);
     
}
