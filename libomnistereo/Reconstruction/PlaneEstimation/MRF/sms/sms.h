#include <mex.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <vector>
#include <map>
#include <limits>

// forward declarations
class Variable;
class Factor;
class Message;

// linear index to subscripts
void ind2sub (int32_t idx, std::vector<int32_t> &dims, std::vector<int32_t> &sub);

// subscripts to linear index
int32_t sub2ind (std::vector<int32_t> &dims, std::vector<int32_t> &sub);

void computeBeliefs (std::vector<Variable*> &variables, bool verbose);

float computeEnergy (std::vector<Variable*> &variables, std::vector<Factor*> &factors, std::vector<int32_t> &map);

void computeSparseMessage (std::vector<Variable*> &variables, std::vector<Factor*> &factors,
                           std::vector<Message*> &msg_v_f, std::vector<float> &msg_min,
                           std::vector<int32_t> state, Message *m,int32_t v_idx,bool verbose);

class Variable {
public:
  Variable (int32_t dim) : dim(dim) {
    belief = (float*)calloc(dim,sizeof(float));
  }
  ~Variable () {
    free(belief);
  }
  int32_t map () {
    int32_t min_idx = 0;
    float min_val = std::numeric_limits<float>::max();
    for (int32_t d=0; d<dim; d++) {
      if (belief[d]<min_val) {
        min_val = belief[d];
        min_idx = d;
      }
    }
    return min_idx; 
  }
  int32_t           dim;    // dimensionality
  float            *belief; // belief vector
  std::vector<Message*>  msg_in; // incoming messages for computing belief
};

class Factor {
public:
  Factor (std::vector<Variable*> &variables,std::vector<int32_t> v,std::vector<float> vals_,int32_t nz_states=0) : v(v), nz_states(nz_states) {
    num_states = 1;
    for (auto &i : v) {
      dims.push_back(variables[i]->dim);
      num_states *= variables[i]->dim;
    }
    vals = (float*)calloc(vals_.size(),sizeof(float));
    for (int32_t i=0; i<vals_.size(); i++)
      vals[i] = vals_[i];
  }
  ~Factor () {
    free(vals);
  }
  inline int32_t sparseState (int32_t idx,int32_t var) {
    return vals[idx*(v.size()+1)+var];
  }
  inline float sparseVal (int32_t idx) {
    return vals[idx*(v.size()+1)+v.size()];
  }
  inline float sparseStateVal (std::vector<int32_t> state) {
    for (int32_t i=0; i<nz_states; i++) {
      bool same_state = true;
      for (int32_t j=0; j<v.size() && j<state.size(); j++) {
        if (sparseState(i,j)!=state[j]) {
          same_state = false;
          break;
        }
      } 
      if (same_state)
        return sparseVal(i);
    }
  }
  // TODO: combine with above function
  inline int32_t sparseStateIdx (std::vector<int32_t> state) {
    for (int32_t i=0; i<nz_states; i++) {
      bool same_state = true;
      for (int32_t j=0; j<v.size() && j<state.size(); j++) {
        if (sparseState(i,j)!=state[j]) {
          same_state = false;
          break;
        }
      } 
      if (same_state)
        return i;
    }
    return -1; // not a special state
  }
  void dump (int32_t f) {
    
    // dump sparse factor
    if (nz_states>0) {
      for (int32_t i=0; i<nz_states; i++) {
        printf("f%d sparse %04d (",f,i);
        for (int32_t j=0; j<v.size(); j++) {
          printf("%d",sparseState(i,j));
          if (j<v.size()-1)
            printf(",");
        }
        printf(") : %.2f\n",sparseVal(i));
      }
      
    // dump dense factor
    } else {
      std::vector<int32_t> sub;
      sub.resize(v.size());
      for (int32_t i=0; i<num_states; i++) {
        ind2sub (i,dims,sub);
        printf("f%d dense %04d (",f,i);
        for (int32_t j=0; j<v.size(); j++) {
          printf("%d",sub[j]);
          if (j<v.size()-1)
            printf(",");
        }
        printf(") : %.2f\n",vals[i]);
      }
    }
  }
  std::vector<int32_t>  v;          // variable indices for this factor
  std::vector<int32_t>  dims;       // number of dimensions of each variable
  int32_t          num_states; // total number of states
  float           *vals;       // potential values
  int32_t          nz_states;  // number of non-zero states (=0 means dense)
};

class Message {
public:
  Message (std::vector<Variable*> &variables,int32_t v, int32_t f, int32_t x, bool v_to_f) : v(v), f(f), x(x), v_to_f(v_to_f) {
    dim = variables[v]->dim; // TODO: Not needed!?
    vals = (float*)calloc(dim,sizeof(float));
    //for (int32_t d=0; d<dim; d++)
      //vals[d] = (float)rand()/(float)RAND_MAX;
  }
  ~Message () {
    free(vals);
  }
  void normalize () {
    float mean = 0;
    for (int32_t d=0; d<dim; d++)
      mean += vals[d];
    mean /= (float)dim;
    for (int32_t d=0; d<dim; d++)
      vals[d] -= mean;// + 0.001*(float)rand()/(float)RAND_MAX;
  }
  void dump () {
    if (v_to_f) printf("message v%d -> f%d:",v,f);
    else        printf("message f%d -> v%d:",f,v);
    for (int32_t i=0; i<dim; i++)
      printf(" %2.2f",vals[i]);
    printf("\n");
  }
  int32_t           v;      // variable index
  int32_t           f;      // factor index
  int32_t           x;      // index of v within factor x
  int32_t           dim;    // dimensionality of message
  float            *vals;   // message values
  bool              v_to_f; // this is a variable to factor message
  std::vector<Message*>  msg_in; // pointer to messages sent to this node
};
