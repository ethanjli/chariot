function I_new = planeImage ( Theta_Dis, Phi_Dis, SP, idx, hypo )

config_360_stereo_image;

if hypo(idx,2) ~= -1

    phi = conversion_360disp_phiD2phi ( Phi_Dis, height);
    alpha = hypo(idx,1);
    d = hypo(idx,2);
    R_hypo = cos( phi - alpha ) ./ d;

else
    
    theta = Theta_Dis ./ (width-1) .* (maxTheta - minTheta) + minTheta;
    z_hypo = hypo(idx,1);
    R_hypo = 1./ ( tan(theta) .* (z_hypo));

end

I_new = zeros(size(SP));
I_new(:) = R_hypo;
