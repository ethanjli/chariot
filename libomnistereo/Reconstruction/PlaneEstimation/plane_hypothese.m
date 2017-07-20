function [R_mat, I_index] = plane_hypothese ( SP, Idis, height, width, minTheta, maxTheta, hypo )

D = Idis;
max_number = max(max(SP));
R_mat = zeros( max_number, size(hypo,1));
I_index = zeros(max_number,1);

% Loop for all superpixels
for i = 1 : max_number
    
   list = find(SP==i);
   
   dis = D(list);
   [Theta_Dis, Phi_Dis] = ind2sub(size(D),list);
   
   if isnan(dis) == 1
        
       R_mat(i,:) = NaN;
   
   else
       
        R_img = dis;
       
        phi = conversion_360disp_phiD2phi ( Phi_Dis, height);
        
        theta = Theta_Dis ./ (width-1) .* (maxTheta - minTheta) + minTheta;
       
        % Loop for all hypotheses ( vertical and horizontal)
        for j = 1 : size(hypo,1)
   
            if hypo(j,2) ~= -1
                
                alpha = hypo(j,1);
                d = hypo(j,2);

                % 1/R
                R_hypo = cos( phi - alpha ) ./ d;
            else
                z_hypo = hypo(j,1);
                
                % 1/R
                R_hypo = 1./ ( tan(theta) .* (z_hypo));
            end
            
            if any(R_hypo<0) 
                R_mat(i,j) = NaN;
            else                
                R_mat(i,j) = nanmean( abs(R_img - R_hypo));
            end
                    
        end
          
	[B,Ix] = min(R_mat(i,:));
   
    I_index(i) = Ix;
      
	end

end




