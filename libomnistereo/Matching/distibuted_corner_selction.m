function corners_new = distibuted_corner_selction ( corners, xc, yc ) 

p = corners{1}.p;
p2 = corners{2}.p;
p3 = corners{3}.p;
p4 = corners{4}.p;

num_array = 16;
num_per_array = 12;

val_1 = [0 : 2*pi/num_array : pi-2*pi/num_array, -2*pi/num_array : -2*pi/num_array : -pi];
val_2 = [2*pi/num_array : 2*pi/num_array : pi, 0 : -2*pi/num_array : -pi-2*pi/num_array];

% compute angle phi
phi = sign(p(:,2)-yc) .* acos( (p(:,1)-xc) ./ sqrt((p(:,1)-xc).^2+(p(:,2)-yc).^2));

ind = 1;

for a = 1 : num_array
    
    idx = find( phi>=val_1(a) & phi<val_2(a));

    if isempty(idx)~=1
        num = min(num_per_array,size(idx,1));
        val = randi([1,size(idx,1)],1,num);
        for m = 1 : num
            corners_new{1}.p(ind,:) = p(idx(val(m)),:);
            corners_new{2}.p(ind,:) = p2(idx(val(m)),:);
            corners_new{3}.p(ind,:) = p3(idx(val(m)),:);
            corners_new{4}.p(ind,:) = p4(idx(val(m)),:);
            ind = ind + 1;
        end
    end
    
end


