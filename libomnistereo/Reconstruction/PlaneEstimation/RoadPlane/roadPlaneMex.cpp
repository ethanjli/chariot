#include <math.h>
#include <vector>
#include <string>
#include <stdint.h>

#include "mex.h"
#include "matrix.h"

using namespace std;

struct tPoint {
  float x,y,z,r;
  tPoint() {}
  tPoint(float x, float y, float z, float r) : x(x), y(y), z(z), r(r) {}
};

struct tPointCloud {
  vector<tPoint>  points;
  vector<float>   parameters;
  vector<int32_t> inliers;
  void clear() {
    points.clear();
    parameters.clear();
    inliers.clear();
  }
};

tPointCloud point_cloud;
std::vector<int32_t> ransacObs;

vector<int32_t> setObservations(int32_t stepsize){
  vector<int32_t> observations;
  for (uint32_t i=0; i<point_cloud.points.size(); i+=stepsize){
    if( point_cloud.points[i].z>-0.5 )
      continue;
    observations.push_back(i);
  }
  
  cout<<point_cloud.points.size() << endl;
  cout << observations.size() << endl; 
  
  return observations;
}

void loadPoints( double* P, int32_t num) {

    cout << num << endl;

  for (int32_t i=0; i<num; i++) {
      
      float x = (float)P[i*3 + 0];
      float y = (float)P[i*3 + 1];
      float z = (float)P[i*3 + 2];
      
      point_cloud.points.push_back( tPoint( x, y, z, 0) ) ;

  }
 
   ransacObs = setObservations(5);
}

vector<int32_t> getRandomSample(vector<int32_t> observations, int32_t num) {

  // init sample
  vector<int32_t> sample;

  // add num indices to current sample
  sample.clear();
  for (int32_t i=0; i<num; i++) {
    if (observations.empty())
      break;

    int32_t j = rand()%observations.size();
    sample.push_back(observations[j]);
    observations.erase(observations.begin()+j);
  }

  // return sample
  return sample;
}

// surface: z=ax+by+c (estimate a,b,c)
bool estimateParameters(vector<int32_t> sample){

  // init matrices
  Matrix A(sample.size(),3);
  Matrix b(sample.size(),1);

  // for all samples do
  for (uint32_t i=0; i<sample.size(); i++) {

    // get observation
    // set matrix entries
    A.val[i][0] = point_cloud.points[sample[i]].x;
    A.val[i][1] = point_cloud.points[sample[i]].y;
    A.val[i][2] = 1;
    b.val[i][0] = point_cloud.points[sample[i]].z;
  }

  // put up least squares system
  Matrix A_ = ~A*A;
  Matrix b_ = ~A*b;

  // gauss jordan elimination successfull?
  if (b_.solve(A_)) {

    point_cloud.parameters[0] = b_.val[0][0];
    point_cloud.parameters[1] = b_.val[1][0];
    point_cloud.parameters[2] = b_.val[2][0];
    return true;

  // otherwise
  } else {
    return false;
  }

  // success
  return true;
}

vector<int32_t> getInliers(vector<int32_t> observations, vector<float> planeParams, float inlier_dist){
  float a = planeParams[0];
  float b = planeParams[1];
  float c = planeParams[2];
  vector<int32_t> curr_inlier;
  for (uint32_t i=0; i < observations.size(); i++)
    if (fabs(   a * point_cloud.points[observations[i]].x
              + b * point_cloud.points[observations[i]].y
              + c - point_cloud.points[observations[i]].z ) < inlier_dist)
      curr_inlier.push_back(observations[i]);
  return curr_inlier;
}

// groundplane RANSAC: input active liste 0...num_points
vector<float> estimateSurface(){

  // minimum number for estimating a plane
  uint32_t minNumObservations = 3;

  // maximum iteration
  int32_t num_iterations = 1000;

  // threshold what belongs to the estimated plane
  float inlier_dist = 0.2;
  float inlier_dist_all = 0.3;

  // inliers and parameters for every RANSAC step, drawn sample
  vector<int32_t> inliers_curr, inliers_best, sample;

  inliers_best.clear();
  point_cloud.parameters.resize(minNumObservations,0);
  vector<float> parameters_best;
  parameters_best.resize(minNumObservations,0);

  // check if there are enough active points (3 parameters)
  if (ransacObs.size()<minNumObservations)
    return parameters_best;

  // for all RANSAC iterations do
  for (int32_t i=0; i<num_iterations; i++){
    
    // draw a set of random samples
    sample = getRandomSample(ransacObs, minNumObservations);

    // estimate surface
    if (estimateParameters(sample)){
      
      // get inliers, and check if we are better
      inliers_curr.clear();
      inliers_curr = getInliers(ransacObs, point_cloud.parameters, inlier_dist);
      if (inliers_curr.size()>inliers_best.size()){
        inliers_best = inliers_curr;
        parameters_best.clear();
        parameters_best = point_cloud.parameters;
      }
    }
  }

  // final fit with all inliers
  if (!inliers_best.empty()){

    // final LS fit
    if(!estimateParameters(inliers_best))
      return parameters_best;
    parameters_best = point_cloud.parameters;
  }
  return parameters_best;
}

void mexFunction (int nlhs,mxArray *plhs[],int nrhs,const mxArray *prhs[]) {

  // check arguments
  if (nrhs!=1)
    mexErrMsgTxt("1 input parameters required (P).");
  if (nlhs!=1)
    mexErrMsgTxt("1 output parameter required (D).");
  if (!mxIsDouble(prhs[0]) || mxGetM(prhs[0])!=3)
    mexErrMsgTxt("Input P must be a 3xN double matrix.");
  
    // input
  double* P =   (double*)mxGetPr(prhs[0]);
  int32_t n =             mxGetN(prhs[0]);
  
  // clear static memory
  point_cloud.clear();
  ransacObs.clear();
  
  // read filename
  //char filename[1024];
  //mxGetString(prhs[0],filename,1024);
  
  // output parameters
  const int dims[] = {1,3};
  plhs[0]          = mxCreateNumericArray(2,dims,mxDOUBLE_CLASS,mxREAL);
  double *param    = (double*)mxGetPr(plhs[0]);
  
  // comput plane
  loadPoints(P,n);
  vector<float> p = estimateSurface();
  param[0] = p[0];
  param[1] = p[1];
  param[2] = p[2];
}
