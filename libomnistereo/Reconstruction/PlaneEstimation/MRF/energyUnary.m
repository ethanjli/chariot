function [E_unary,F_unary] = energyUnary (m,SP,PlaneHypos,Idis,meanI,stdI,clip_val,maxval)

% avoid division by 0!
stdI(stdI<0.001) = nan;

num_superpx = double(max(SP(:)));
num_planes = size(PlaneHypos,1);

% compute unary energies
E_unary = zeros([num_superpx num_planes]);
F_unary = zeros([num_superpx num_planes]);

[Theta_Dis, Phi_Dis] = ind2sub(size(SP),1:numel(SP));

for i=1:num_planes
  P = planeImage(Theta_Dis,Phi_Dis,SP,i,PlaneHypos);
  E = min(abs(P-Idis),clip_val);
  F = 0.01*abs(P-meanI)./stdI;
  E(P<0) = nan;
  for j=1:num_superpx
    e_sum = sum(E(m{j}));
    if isnan(e_sum)
      E_unary(j,i) = maxval;
    else
      E_unary(j,i) = e_sum;
    end
    f_sum = sum(F(m{j}));
    if isnan(f_sum)
      F_unary(j,i) = 0;
    else
      F_unary(j,i) = f_sum;
    end
  end
end
