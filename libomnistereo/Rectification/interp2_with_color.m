function new_img = interp2_with_color ( U, V, img, Qu1, Qv1, method)

r1 = interp2(U, V, shiftdim(img(:,:,1)), Qu1, Qv1, method);
g1 = interp2(U, V, shiftdim(img(:,:,2)), Qu1, Qv1, method);
b1 = interp2(U, V, shiftdim(img(:,:,3)), Qu1, Qv1, method);
            
new_img(:,:,1) = r1(:,:)';
new_img(:,:,2) = g1(:,:)';
new_img(:,:,3) = b1(:,:)';
            
% behind_left_colored  = behind_left_colored(:,:,:)';
%             behind_right_colored = behind_right_colored(:,:,:)';
end
            