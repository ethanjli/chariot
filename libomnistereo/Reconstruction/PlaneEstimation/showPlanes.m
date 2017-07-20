function I_new = showPlanes ( SP, I_index, hypo )

config_360_stereo_image;

max_number = max(max(SP));

I_new = zeros(size(SP));

% Loop for all superpixels
for i = 1 : max_number

    list = find(SP==i);
    
    [Theta_Dis, Phi_Dis] = ind2sub(size(SP),list);

    Ix = I_index(i);
    
    if Ix > 0

        if hypo(Ix,2) ~= -1

            phi = conversion_360disp_phiD2phi ( Phi_Dis, height);
        
            alpha = hypo(Ix,1);
            d = hypo(Ix,2);

            % 1/R
            R_hypo = cos( phi - alpha ) ./ d;
         else

            theta = Theta_Dis ./ (width-1) .* (maxTheta - minTheta) + minTheta;

            z_hypo = hypo(Ix,1);

            % 1/R
            R_hypo = 1./ ( tan(theta) .* (z_hypo));
        end

        if any(R_hypo<0) 
            I_new(list) = 0;
        else                
            I_new(list) = R_hypo;
        end

    else 
        I_new(list) = 0;
    end
  

end

if nargout==0
  figure;
  imagesc(I_new);
  colormap(jet(1024))
end
