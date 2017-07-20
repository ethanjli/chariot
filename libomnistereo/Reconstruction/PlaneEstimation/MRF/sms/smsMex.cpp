#include "sms.h"

// TODOs:
// - sparse input indices must be 1-based (states)! (change all m files!)
// - variables is rather num_states (input)
// - dims is often num_states as well
// - check input (also cellarray and structs)
// - put linear index to subscripts to Factor class?
// - remove dimensionality of message? maybe as a function!
// - create unit test for "brute-forcing"
// - test this (random unit tests) for multiple special states!!
// - bug with letter higher-order when specified as separate potentials ..

using namespace std;

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {
  
  if (nrhs!=3 && nrhs!=4)
    mexErrMsgTxt("3 or 4 inputs required: variables,factors,iters[,verbose]");
  if (nlhs!=1)
    mexErrMsgTxt("1 output required (map)");
  if (!mxIsDouble(prhs[0]) || mxGetM(prhs[0])!=1)
    mexErrMsgTxt("variables must be a 1xN double vector");
  if (!mxIsCell(prhs[1]))
    mexErrMsgTxt("factors must be a structure");
  if (!mxIsDouble(prhs[2]) || mxGetM(prhs[2])*mxGetN(prhs[2])!=1)
    mexErrMsgTxt("iters must be a double scalar");
  
  // get number of iterations and verbosity level
  int32_t num_iters = (int32_t)(*(double*)mxGetPr(prhs[2]));
  int32_t verbose = 0;
  if (nrhs==4) {
    if (!mxIsDouble(prhs[3]) || mxGetM(prhs[3])*mxGetN(prhs[3])!=1)
      mexErrMsgTxt("verbose must be a double scalar");
    verbose = (int32_t)(*(double*)mxGetPr(prhs[3]));
  }
  
  // random number generator seed
  srand(time(0));
  
  // init variables & factors
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
  
  if (verbose>=2)
    for (int32_t f=0; f<factors.size(); f++)
      factors[f]->dump(f);
  
  // init messages and helper maps
  vector<Message*> msg_v_f;
  vector<Message*> msg_f_v;
  map<int32_t,vector<Message*>> msg_to_factor;
  map<int32_t,vector<Message*>> msg_to_variable;
  for (int32_t f=0; f<factors.size(); f++) {
    Message *m;
    int32_t x=0;
    for (auto &v : factors[f]->v) {
      m = new Message(variables,v,f,x,true);
      msg_v_f.push_back(m);
      msg_to_factor[f].push_back(m);
      m = new Message(variables,v,f,x,false);
      msg_f_v.push_back(m);
      msg_to_variable[v].push_back(m);
      x++;
    }
  }
  
  // set incoming message pointers
  for (auto &m : msg_v_f) m->msg_in = msg_to_variable[m->v];  
  for (auto &m : msg_f_v) m->msg_in = msg_to_factor[m->f];
  for (int32_t v=0; v<variables.size(); v++)
    variables[v]->msg_in = msg_to_variable[v];
   
  // for all iterations do
  float energy_min = numeric_limits<float>::max();
  vector<int32_t> map_min;
  for (int32_t iter=0; iter<num_iters; iter++) {

    // iterate over factor-to-variable messages
    for (auto &m : msg_f_v) {

      // init minima to large values
      for (int32_t d=0; d<variables[m->v]->dim; d++)
        m->vals[d] = numeric_limits<float>::max();
      
      // sparse representation
      if (factors[m->f]->nz_states>0) {
        
        // pre-compute message minima
        vector<float> msg_min;
        for (auto &m_in : m->msg_in) {
          float min_val = numeric_limits<float>::max();
          for (int32_t d=0; d<m_in->dim; d++)
            if (m_in->vals[d]<min_val)
              min_val = m_in->vals[d];
          msg_min.push_back(min_val);
        }
        
        // init state and start recursion
        vector<int32_t> state;
        state.resize(factors[m->f]->v.size(),0);
        computeSparseMessage(variables,factors,msg_v_f,msg_min,state,m,0,verbose);
        
      // dense representation
      } else {

        // loop over all states of associated factor
        vector<int32_t> sub;
        sub.resize(factors[m->f]->dims.size());
        for (int32_t idx=0; idx<factors[m->f]->num_states; idx++) {

          // get subscripts from linear index
          ind2sub (idx, factors[m->f]->dims, sub);

          // loop over variables involved in this factor
          float sum = factors[m->f]->vals[idx];
          for (int32_t i=0; i<factors[m->f]->v.size(); i++)
            if (i!=m->x)
              sum += m->msg_in[i]->vals[sub[i]];

          int32_t d = sub[m->x];
          m->vals[d] = min(m->vals[d],sum);
        }
      }
      
      // normalize message
      //m->normalize();
      if (verbose>=2)
        m->dump();
    }

    // iterate over variable-to-factor messages
    for (auto &m : msg_v_f) {

      // loop over all dimensions
      for (int32_t d=0; d<variables[m->v]->dim; d++) {

        // loop over factors involved in this variable
        float sum = 0;
        for (int32_t i=0; i<m->msg_in.size(); i++)
          if (m->msg_in[i]->f!=m->f)
            sum += m->msg_in[i]->vals[d];
        m->vals[d] = sum;
      }
      //m->normalize();
      if (verbose>=2)
        m->dump();
    }
        
    // compute energy from current map estimate
    computeBeliefs (variables,verbose);
    vector<int32_t> map;
    float energy = computeEnergy (variables,factors,map);
    if (energy<energy_min) {
      energy_min = energy;
      map_min = map;
    }
    
    // output
    if (verbose>=1) {
      printf("Iteration: % 3d, Energy: %.3f\n",iter,energy);
      mexEvalString("drawnow;");
    }
  }
  
  if (verbose>=2) {
    printf("Beliefs:\n");
    mexEvalString("drawnow;");
  }
  
  // set map state
  for (int32_t v=0; v<variables.size(); v++)
    map_mex[v] = map_min[v]+1;
  
  // release memory
  for (int32_t i=0; i<variables.size(); i++) delete variables[i];
  for (int32_t i=0; i<factors.size();   i++) delete factors[i];
  for (int32_t i=0; i<msg_v_f.size();   i++) delete msg_v_f[i];
  for (int32_t i=0; i<msg_f_v.size();   i++) delete msg_f_v[i];
}
