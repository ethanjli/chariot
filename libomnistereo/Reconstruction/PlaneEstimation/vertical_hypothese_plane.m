function [alpha, d] = vertical_hypothese_plane ( alpha_ind, alpha_scale, d_ind, d_scale)

alpha = (alpha_ind ./ alpha_scale * (2*pi)); 

d = (d_ind-1)/d_scale;