#include <mex.h>
#include <vector>
#include <algorithm> // for set_intersection
#include <math.h>    // for M_PI
#include <cmath>     // for abs(double)

using namespace std;

// extracts boundary pixels to vector<int> (0-based)
inline vector<int> boundaryPixels (const mxArray *SP_bnd, int32_t idx) {
  mxArray *SP_bnd_idx = mxGetCell(SP_bnd,idx);
  int32_t n = mxGetM(SP_bnd_idx);
  double* vals = (double*)mxGetPr(SP_bnd_idx);
  vector<int> bp; bp.resize(n);
  for (int i=0; i<n; i++)
    bp[i] = vals[i]-1; // convert to 0-based index
  return bp;
}

inline float disparity (float u, float v, float a, float b) {
  
  // init disparity
  float d;
  
  // vertical plane
  if (b>-0.5) {
    float phi = (u/999.0) * 2.0 * M_PI - M_PI;
    d = cos(phi-a)/b;
    
  // horizontal plane
  } else {
    float theta = (v/499.0) * 1.3963 + 1.3090;
    d = 1.0/(tan(theta)*a);
  }
  
  // return disparity
  return d;
}

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {
  
  if (nrhs!=4)
    mexErrMsgTxt("4 inputs required: SP_adj,SP_bnd,Planes,clip_val]");
  if (nlhs!=1)
    mexErrMsgTxt("1 output required (E_pair)");
  if (!mxIsDouble(prhs[0]))
    mexErrMsgTxt("SP_adj must be a double matrix");
  if (!mxIsCell(prhs[1]))
    mexErrMsgTxt("SP_bnd must be a cell array");
  if (!mxIsDouble(prhs[2]))
    mexErrMsgTxt("Planes must be a double matrix");
  
  int ns = mxGetM(prhs[0]); // number of superpixels
  int np = mxGetM(prhs[2]); // number of planes
  
  // get pointers to input
  double *SP_adj = (double*)mxGetPr(prhs[0]);
  const mxArray *SP_bnd = prhs[1];
  double *Planes = (double*)mxGetPr(prhs[2]);
  double clip_val = *((double*)mxGetPr(prhs[3]));
  
  // image height
  int img_height = 300;
  
  // create output cell array (pairwise energies)
  int E_pair_dims[2] = {ns,ns};
  plhs[0] = mxCreateCellArray(2,E_pair_dims);

  // for all superpixels do
  for (int i=0; i<ns; i++) {
    
    // get boundary pixel indices for superpixel i
    vector<int> bp_i = boundaryPixels(SP_bnd,i);

    // for all other superpixels do
    for (int j=i+1; j<ns; j++) {
      
      // if superpixels are adjacent
      if (SP_adj[j*ns+i]>0.5) {
        
        // get boundary pixel indices for superpixel j
        vector<int> bp_j = boundaryPixels(SP_bnd,j);
        
        // compute indices of intersecting boundary pixels
        // important note: this assumes that the inputs bp_i and bp_j are sorted!!
        vector<int> bp_int(bp_i.size()+bp_j.size());
        vector<int>::iterator it;
        it = set_intersection (bp_i.begin(),bp_i.end(),bp_j.begin(),bp_j.end(),bp_int.begin());
        bp_int.resize(it-bp_int.begin());
        int bp_num = bp_int.size();
        
        // find indices k1 and k2 (within bp_int) of most distant boundary points
        double max_dist = 0; int max_k1 = 0; int max_k2 = 0;
        for (int k1=0; k1<bp_num; k1++) {
          for (int k2=k1+1; k2<bp_num; k2++) {

            // extract u and v image coordinates
            // note: 1-based index is calculated as planes are represented
            //       using MATLAB 1-based indices
            double u1 = bp_int[k1]/img_height+1;
            double v1 = bp_int[k1]%img_height+1;
            double u2 = bp_int[k2]/img_height+1;
            double v2 = bp_int[k2]%img_height+1;
            double du = u1-u2;
            double dv = v1-v2;
            double dist2 = du*du+dv*dv;
            
            // update if boundary points are further apart
            if (dist2>max_dist) {
              max_dist = dist2;
              max_k1 = k1;
              max_k2 = k2;
            }
          }
        }
        
        // approximate the bp_int with 2 points
        vector<int> bp_int_sparse;
        bp_int_sparse.push_back(bp_int[max_k1]);
        bp_int_sparse.push_back(bp_int[max_k2]);
        
        // create output
        int E_dims[2] = {np,np};
        mxArray* E = mxCreateNumericArray(2,E_dims,mxDOUBLE_CLASS,mxREAL);
        double* E_vals = (double*)mxGetPr(E);

        // for all planes in first superpixel do
        for (int pi=0; pi<np; pi++) {
          
          // extract plane parameters for first superpixel
          double a1 = Planes[pi];
          double b1 = Planes[np+pi];
        
          // for all planes in second superpixel do
          for (int pj=0; pj<np; pj++) {
          
            // extract plane parameters for second superpixel
            double a2 = Planes[pj];
            double b2 = Planes[np+pj];
            
            // compute accumulated truncated l1 disparity error
            double e = 0;
            
            // for all boundary pixels (pixels of intersection) do
            for (int k=0; k<bp_int_sparse.size(); k++) {
              
              // extract u and v image coordinates
              // note: 1-based index is calculated as planes are represented
              //       using MATLAB 1-based indices
              double u = bp_int_sparse[k]/img_height+1;
              double v = bp_int_sparse[k]%img_height+1;
              
              // compute disparity values given both plane hypotheses
              double d1 = disparity(u,v,a1,b1);
              double d2 = disparity(u,v,a2,b2);
              
              // accumulate truncated l1 disparity error
              e += min(abs(d1-d2),clip_val);
            }
            
            // set error (multiply by bp_num/2 due to sparse approximation)
            E_vals[pj*np+pi] = e*(double)bp_num/2.0;
          }
        }

        // set energy values in cell corresponding to superpixel (i,j)
        int subs[2] = {i,j};
        int idx = mxCalcSingleSubscript(plhs[0],2,subs);
        mxSetCell(plhs[0],idx,E);
      }
    }
  }
}
