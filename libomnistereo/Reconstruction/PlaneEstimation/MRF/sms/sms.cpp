#include "sms.h"

using namespace std;

// linear index to subscripts
void ind2sub (int32_t idx, vector<int32_t> &dims, vector<int32_t> &sub) {
  for (int32_t i=0; i<dims.size(); i++) {
    sub[i] = idx % dims[i];
    idx /= dims[i];
  }
}

// subscripts to linear index
int32_t sub2ind (vector<int32_t> &dims, vector<int32_t> &sub) {
  int32_t idx = 0;
  for (int32_t i=dims.size()-1; i>=0; i--)
    idx = idx*dims[i]+sub[i];
  return idx;
}

void computeBeliefs (vector<Variable*> &variables, bool verbose) {
  
  // iterate over variables
  for (int32_t v=0; v<variables.size(); v++) {

    // loop over all dimensions
    for (int32_t d=0; d<variables[v]->dim; d++) {

      // loop over factors involved in this variable
      float sum = 0;
      for (auto &m : variables[v]->msg_in)
        sum += m->vals[d];
      variables[v]->belief[d] = sum;
      if (verbose>=2)
        printf("v%d:%d %.2f\n",v,d,variables[v]->belief[d]);
    }
  }
}

float computeEnergy (vector<Variable*> &variables, vector<Factor*> &factors, vector<int32_t> &map) {
  
  // pre-compute map estimates
  map = vector<int32_t>(variables.size());
  for (int32_t v=0; v<variables.size(); v++)
    map[v] = variables[v]->map();
  
  // compute energy from factors
  float energy = 0;
  for (auto &f : factors) {
    
    vector<int32_t> state;
      for (auto &v : f->v)
        state.push_back(map[v]);
    
    // sparse representation
    if (f->nz_states>0) {
        
      energy += f->sparseStateVal(state);      
      
    // dense representation
    } else {
      energy += f->vals[sub2ind(f->dims,state)];
    }
  }
  
  // return energy
  return energy;
}

void printState (const char *desc,vector<int32_t> &state,int32_t v_idx) {
  printf("%s: state=",desc);
  printf("(");
  for (int32_t i=0; i<state.size(); i++) {
    printf("%d",state[i]);
    if (i<state.size()-1)
      printf(",");
  }
  printf(")");
  printf(" v_idx=%d\n",v_idx);
  mexEvalString("drawnow;");
}

void computeSparseMessage (vector<Variable*> &variables, vector<Factor*> &factors,
                           vector<Message*> &msg_v_f, vector<float> &msg_min,
                           vector<int32_t> state, Message *m,int32_t v_idx,bool verbose) {
  
  // get reference to factor involved in this message
  Factor* f = factors[m->f];
  
  // update minima for composite state or continue recursion
  if (v_idx<state.size()) {
    
    // is a special state included in this set of states?
    bool any_special_state_included = false;
    for (int32_t i=0; i<f->nz_states; i++) {
      
      // is this state included
      bool curr_special_state_included = true;
      for (int32_t j=0; j<v_idx; j++) {
        if (f->sparseState (i,j)!=state[j]) {
          curr_special_state_included = false;
          break;
        }
      }
      
      // if current special state is included break
      if (curr_special_state_included) {
        any_special_state_included = true;
        break;
      }
    }
    
    // if any special state is included continue recursion
    if  (any_special_state_included) {
    //if  (any_special_state_included || 1) {
      
      for (int32_t d=0; d<f->dims[v_idx]; d++) {
        state[v_idx] = d;
        computeSparseMessage (variables,factors,msg_v_f,msg_min,state,m,v_idx+1,verbose);
      }
    
    // otherwise update minima for composite state
    } else {
      
      if (verbose>=2)
        printState("composite",state,v_idx);
      
      // init sum (no special state involved => no factor contribution)
      float sum = 0;
      for (int32_t i=0; i<state.size(); i++) {

        // TODO: when recursing, m->x could/should (?) be jumped over!!
        // maybe not as otherwise special state updates are not complete? think!!
        if (i!=m->x) {
          if (i<v_idx) sum += m->msg_in[i]->vals[state[i]];
          else         sum += msg_min[i];
        }
      }
      
      // update
      if (v_idx<=m->x) {
        for (int32_t i=0; i<f->dims[m->x]; i++)
          m->vals[i] = min(m->vals[i],sum);
      } else {
        m->vals[state[m->x]] = min(m->vals[state[m->x]],sum);
      }
    }
  
  // update minimum for special state
  } else {
    
    if (verbose>=2)
      printState("special",state,v_idx);

    // init sum to 0 or special state
    int32_t idx = f->sparseStateIdx (state);
    float sum = f->sparseVal(idx);
    
    // add incoming messages except for x
    for (int32_t i=0; i<f->v.size(); i++)
      if (i!=m->x)
        sum += m->msg_in[i]->vals[state[i]];
    
    // update minimum at x
    m->vals[state[m->x]] = min(m->vals[state[m->x]],sum);
  }
}
