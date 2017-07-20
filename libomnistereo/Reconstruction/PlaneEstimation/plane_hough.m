function H = plane_hough ( Idis, P_hor, folder, frame_number, height, max_dist, d_scale, index, H, debug_flag, save_debug_flag)

for n = 1: index : 1000 
    for m = 1 : index : 300 

        if Idis(m,n) ~= 0 && isnan(P_hor(m,n)) == 0
        
            r = 1./Idis(m,n);

            alpha = [0 : pi/250 : 2*pi]; 
            
            phi_i = ((n ./ (height-1) * (2*pi)) - pi);
             
            d = r .* cos( phi_i - alpha ); 
             
            %figure(7); plot(d); hold on;
            [b,ix] = find(d>0&d<max_dist);
            H((ix-1)*121+round(d(ix)*d_scale+1)) = H((ix-1)*121+round(d(ix)*d_scale+1)) + (1-P_hor(m,n));
           
        end    
    end
end

if (debug_flag)
    figure(6); imagesc(H);
end
if save_debug_flag
    HoughV = H;
    save( sprintf('%sHoughV.mat', folder), 'HoughV');
end

end