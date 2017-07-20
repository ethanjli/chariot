#include "sms.h"

// TODOs:
// - merge variable and factor creation with smsMex.cpp

using namespace std;

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {
  
  if (nrhs!=2 && nrhs!=3)
    mexErrMsgTxt("2 or 3 inputs required: variables,factors[,verbose]");
  if (nlhs!=1)
    mexErrMsgTxt("1 output required (map)");
  if (!mxIsDouble(prhs[0]) || mxGetM(prhs[0])!=1)
    mexErrMsgTxt("variables must be a 1xN double vector");
  if (!mxIsCell(prhs[1]))
    mexErrMsgTxt("factors must be a structure");
  
  // get verbosity level
  int32_t verbose = 0;
  if (nrhs==3) {
    if (!mxIsDouble(prhs[2]) || mxGetM(prhs[2])*mxGetN(prhs[2])!=1)
      mexErrMsgTxt("verbose must be a double scalar");
    verbose = (int32_t)(*(double*)mxGetPr(prhs[2]));
  }
  
  // init variables, factors, verbosity level
  vector<Variable*> variables;
  vector<Factor*> factors;
  
  // create variables 
  int32_t n_var = mxGetN(prhs[0]);
  double* dim_mex = (double*)mxGetPr(prhs[0]);
  for (int32_t v=0; v<n_var; v++)
    variables.push_back(new Variable(dim_mex[v]));
  
  // create factors
  int32_t n_fac = mxGetN(prhs[1]);
  for (int32_t f=0; f<n_fac; f++) {
    mxArray *f_cell  = mxGetCell(prhs[1],f);
    mxArray *v_field = mxGetField(f_cell,0,"v");
    mxArray *e_field = mxGetField(f_cell,0,"e");
    mxArray *s_field = mxGetField(f_cell,0,"s");
    bool sparse;
    if (e_field && !s_field) {
      sparse = false;
    } else if (s_field && !e_field) {
      sparse = true;
      e_field = s_field;
    } else {
      mexErrMsgTxt("mixed sparse/dense factors are not allowed!");
    }
    double* v_mex = (double*)mxGetPr(v_field);
    double* e_mex = (double*)mxGetPr(e_field);
    int32_t m = mxGetM(e_field);
    int32_t n = mxGetN(e_field);
    int32_t n_var_fac = mxGetN(v_field);
    
    // extract variables and compute number of possible states
    int32_t num_states = 1;
    vector<int32_t> v_vals;
    for (int32_t i=0; i<n_var_fac; i++) {
      int32_t v_idx = (int32_t)v_mex[i]-1;
      v_vals.push_back(v_idx);
      num_states *= variables[v_idx]->dim;
    }
    
    // create sparse factor
    if (sparse) {
      vector<float> e_vals;
      if (m==0)
        mexErrMsgTxt("sparse factor has no special state");
      if (n!=n_var_fac+1)
        mexErrMsgTxt("sparse factor has wrong number of columns in s");
      for (int32_t i=0; i<m; i++) // #rows = #special states
        for (int32_t j=0; j<n; j++) { // columns: (state,energy value)
          float e_val = (float)e_mex[j*m+i]; // convert to 0-based index
          if (j<n-1) e_val -= 1.0;
          e_vals.push_back(e_val);
        }
      factors.push_back(new Factor(variables,v_vals,e_vals,m));
      
    // create dense factor
    } else {
      if (m!=1)
        mexErrMsgTxt("dense factor e must be exactly single row vector");
      if (n!=num_states)
        mexErrMsgTxt("dense factor e must be of size #states");
      vector<float> e_vals;
      for (int32_t i=0; i<mxGetN(e_field); i++)
        e_vals.push_back((float)e_mex[i]);
      factors.push_back(new Factor(variables,v_vals,e_vals));
    }
  }
  
  // create output
  int32_t map_dims_mex[2] = {1,n_var};
  plhs[0] = mxCreateNumericArray(2,map_dims_mex,mxDOUBLE_CLASS,mxREAL);
  double* map_mex = (double*)mxGetPr(plhs[0]);
  
  // compute number of states and dimensionality of variables
  vector<int32_t> dims;
  vector<int32_t> state;
  state.resize(variables.size(),0);
  int32_t num_states = 1;
  for (auto &v : variables) {
    dims.push_back(v->dim);
    num_states *= v->dim;
    if (num_states>10000000)
      mexErrMsgTxt("can't solve problems with more than 10 mio states");
  }
  if (verbose>=1) {
    printf("brute force: #states=%d #factors=%d\n",num_states,factors.size());
    mexEvalString("drawnow;");
  }
  
  // init min state index and energy
  int32_t i_min = 0;
  float   e_min = std::numeric_limits<float>::max();
  
  // for all states do
  for (int32_t i=0; i<num_states; i++) {
    
    // convert i to state
    ind2sub(i,dims,state);
    
    // sum factors
    float e_curr = 0;
    for (auto &f : factors) {
      
      // convert state to factor_state
      vector<int32_t> factor_state;
      for (auto &v : f->v)
        factor_state.push_back(state[v]);
      
      // sparse factor
      if (f->nz_states>0) {
        
        // add factor if state is one of its special states
        int32_t idx = f->sparseStateIdx(factor_state);
        if (idx>=0)
          e_curr += f->sparseVal(idx);
        
      // dense factor
      } else {
        
        // add factor according to its state
        int32_t idx = sub2ind(f->dims,factor_state);
        e_curr += f->vals[idx];
      }
    }
    
    // update minimum
    if (e_curr<e_min) {
      e_min = e_curr;
      i_min = i;
      if (verbose>=1) {
        printf("state: %d,energy: %F\n",i_min,e_min);
        mexEvalString("drawnow;");
      }
    }
  }
  
  // set map state
  ind2sub(i_min,dims,state);
  for (int32_t v=0; v<variables.size(); v++)
    map_mex[v] = state[v]+1;
  
  // release memory
  for (int32_t i=0; i<variables.size(); i++) delete variables[i];
  for (int32_t i=0; i<factors.size();   i++) delete factors[i];
}
