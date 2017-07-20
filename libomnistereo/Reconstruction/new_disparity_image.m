%% Point Cloud in one disparity image
% 360° Disparity Image
% Input:
% [] - than the mentioned parameters are used
% or
% S - Point Cloud
% seq - number of the sequence


function [ Idis_new, Img_new, phi, theta] = new_disparity_image ( S, save_folder, frame_number, width, height, ... 
    max_visible_theta, save_name, minTheta, maxTheta, velodyne )

% compute [r,phi,theta] - from [x, y, z]
phi = sign(S(2,:)) .* acos( S(1,:) ./ sqrt(S(1,:).^2+S(2,:).^2) );
theta = sign( sqrt(S(1,:).^2 + S(2,:).^2) ) .* acos ( S(3,:) ./ sqrt(S(1,:).^2 + S(2,:).^2 + S(3,:).^2));
r = sqrt( S(1,:).^2 + S(2,:).^2 + S(3,:).^2);

if size(S,1) == 6
    Snew = [ r', phi', theta', S(4:6,:)'];
else
    Snew = [ r', phi', theta', S(4,:)'];
end

%
[phi_dis, theta_dis] = conversion_360disp_angle2angleD ( phi, height, theta, width, minTheta, maxTheta);

Z = sqrt( S(1,:).^2 + S(2,:).^2 );

Img = zeros(width,height);
Idis = zeros(width,height);
Idis_new = zeros(width,height);
Img_new = zeros(width,height);


    theta_dis2 = theta_dis(theta_dis+1<=size(Img,1)&theta_dis+1>=1);
    phi_dis2 = phi_dis(theta_dis+1<=size(Img,1)&theta_dis+1>=1);
    Z2 = Z(theta_dis+1<=size(Img,1)&theta_dis+1>=1);
    Snew2 =  Snew(theta_dis+1<=size(Img,1)&theta_dis+1>=1,:);
    
    theta_phi = sub2ind(size(Idis),theta_dis2+1,phi_dis2+1);
    
    [uniqueID,~,uniqueInd]=unique(theta_phi');
    uniZ = [uniqueID accumarray(uniqueInd,Z2')./accumarray(uniqueInd,1)];
   
    Idis(uniZ(:,1)) = uniZ(:,2);
	
    r = ones(width,height);
    g = ones(width,height);
    b = ones(width,height);
    
    uniS1 = [uniqueID accumarray(uniqueInd,Snew2(:,4)')./accumarray(uniqueInd,1)];
    r(uniS1(:,1)) = uniS1(:,2);
    if size(Snew,2) == 6
        uniS2 = [uniqueID accumarray(uniqueInd,Snew2(:,5)')./accumarray(uniqueInd,1)];
        uniS3 = [uniqueID accumarray(uniqueInd,Snew2(:,6)')./accumarray(uniqueInd,1)];
        g(uniS2(:,1)) = uniS2(:,2);
        b(uniS3(:,1)) = uniS3(:,2);
    end
    
    Img_(:,:,1) = r; Img_(:,:,2) = g; Img_(:,:,3) = b;
    
        
    Idis_new = 1./(Idis(1:max_visible_theta,:));
    Img_new = Img_(1:max_visible_theta,:,:);
    
    imwrite( Idis_new, sprintf('%sIdis%s_%06d.png', save_folder, save_name, frame_number ));
    imwrite( Img_new, sprintf('%sImg%s_%06d.png',save_folder, save_name, frame_number ));

    Idis_color = disp_to_color(Idis_new, 0.6);
    imwrite( Idis_color, sprintf('%sIdis_color%s_%06d.png', save_folder, save_name, frame_number ));

