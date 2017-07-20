function HT = plane_hough_horizontal ( Idis, P_hor, folder, width, d_scale, index, HT, minTheta, maxTheta, debug_flag, save_debug_flag)

for n = 1: index : 1000 
    for m = 1 : index : 300

        if Idis(m,n) ~= 0 && isnan(P_hor(m,n)) == 0
            
            r = 1./Idis(m,n);

            theta = m ./ (width-1) .* (maxTheta-minTheta) + minTheta;
             
            d = r./ tan( theta ); 
                
            if round(abs(d)*10+1) <= 50
                HT(round(abs(d)*d_scale+1)) = HT(round(abs(d)*d_scale+1),1) + P_hor(m,n); 
            end
        end
    
    end
end


if ( debug_flag)
    figure; imagesc(HT);
end

if (save_debug_flag)
    HoughH = HT;
    save( sprintf('%sHoughH.mat', folder), 'HoughH');
end

end