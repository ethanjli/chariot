%% conifg_MRF
%% Parameter for MRF
save_flag_mat = 0;

plane_threshold = 150;

paramsM = [];
paramsM.unary.clipval = 0.050;
paramsM.pairwise.clipval = 0.079;
paramsM.unary.w1 = 1.220;
paramsM.unary.w2 = 1.000;
paramsM.unary.w3 = 0.0;