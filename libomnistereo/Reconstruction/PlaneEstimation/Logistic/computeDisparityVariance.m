function D_var = computeDisparityVariance(D)

fs = 40;

% compute vertical variance
D_var = nan(size(D));
for u=1:size(D,2)
  for v=1:size(D,1)-fs
    D_sub = D(v:v+fs,u);
    d_sub = D_sub(:);
    d_val = d_sub(~isnan(d_sub));
    if length(d_val)>fs/2
      d_var = 1000*var(d_val);
      D_var(v,u) = d_var;
    end
  end
end
D_var(D_var>1) = 1;

% aggregate minimum
D_var_min = D_var;
for v=2:fs
  D_var_min(v+(1:end-fs),:) = min(D_var_min(v+(1:end-fs),:),D_var(1:end-fs,:));
end
D_var = D_var_min;

% set invalid entries to nan
D_var(isnan(D)) = nan;
