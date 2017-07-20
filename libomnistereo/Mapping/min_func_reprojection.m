function [F, J] = min_func_reprojection (xx, param, vec, u_ini, S, method, cams, motion_flag, point_flag)
 
	if motion_flag == 1 && point_flag == 0 
        X = S(:,vec(:));
    elseif motion_flag == 0 && point_flag ==1
        X = reshape( xx(1:end), 3, size(vec,2));
    elseif motion_flag == 1 && point_flag == 1
        X = reshape( xx(1:end-6), 3, size(vec,2));
    end
        
    if any(cams==4) == 1      
        %case 4
        param.cam{3}.ex_T = xx(end-5:end-3); 
        param.cam{3}.ex_om = xx(end-2:end)'; 
        
        Rex =  rodriguesMex(param.cam{2}.ex_om);
        Hex = [ Rex(1:3,1:3), param.cam{2}.ex_T; 0 0 0 1];
        
        Rm = rodriguesMex(xx(end-2:end)');
        Hm = [ Rm(1:3,1:3), xx(end-5:end-3); 0 0 0 1];
        
        H = Hex * Hm;
        param.cam{4}.ex_om = rodrigues( H(1:3,1:3))';
        param.cam{4}.ex_T = H(1:3,4);
            
    elseif any(cams==3) == 1
        %case 3 
        param.cam{3}.ex_T = xx(end-5:end-3);
        param.cam{3}.ex_om = xx(end-2:end)';   
    
    end

    if method == 14                                                         %not published
        
        u = reprojection_centered ( param, X, cams);
        
    else                                                                    %not published
        %[u,J] = reprojection (param, X, method, cams);                     %not published
        u = reprojection (param, X, method, cams);                          %not published
    end                                                                     %not published
        
    F = u' - u_ini;
   
end

