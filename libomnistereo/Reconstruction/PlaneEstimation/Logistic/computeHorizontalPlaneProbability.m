function P_hor = computeHorizontalPlaneProbability(D_var,glm)

% apply glm
d_val = find(D_var>=0);
D_var(d_val) = glmval(glm,D_var(d_val),'logit');
P_hor = D_var;
