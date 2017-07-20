function plane_idx = planeInference( SP, Idis, PlaneHypos, meta_dir, params, verbose)

maxval = 10000; % max energy (=infinity)

if verbose          
  fprintf('Processing: %s\n',frame_dir); 
end                

% load meta data
load([meta_dir '/err_img_2.mat']);
load([meta_dir '/horis_prior.mat']);
load([meta_dir '/meanI.mat']);
load([meta_dir '/stdI.mat']);
  
num_superpx = double(max(SP(:)));
num_planes = size(PlaneHypos,1);
if verbose
  fprintf('Number of planes: %d\n',num_planes);
end

if verbose
  fprintf('Computing superpixel masks ... \n');
end
[M,m] = superpixel_masks(SP);

if verbose
  fprintf('Computing superpixel boundaries ... \n');
end
SP_adj = superpixel_adjacencies(SP);
SP_bnd = superpixel_boundaries(M,SP);

if verbose
  fprintf('Computing unary energies ... \n');
end
[E_unary,F_unary] = energyUnary(m,SP,PlaneHypos,Idis,meanI,stdI,params.unary.clipval,maxval);

if verbose
  fprintf('Computing pairwise energies ... \n');
end
E_pair = energyPairwiseMex(SP_adj,SP_bnd,PlaneHypos,params.pairwise.clipval);

% setting up MRF
if verbose
  fprintf('Setting up CRF ... \n');
end

% init variables and factors
variables = ones(1,num_superpx)*num_planes;
factors = []; k = 1;

% pre-compute horizontal plane i
hor = 2*double((PlaneHypos(:,2)==-1))' - 1;

% superpixel potentials (unary)
for i=1:num_superpx
  
  % weighted disparity
  d = Idis(m{i}); % disparity values
  q = errN(m{i}); % matching quality
  w = mean(q);% * sum(~isnan(d))/length(d);
  %w = 1;%sum(~isnan(d))/length(d);
  % good idea? parameterize this?
  e1 = w*E_unary(i,:);%+0.1*rand(1,num_planes); % add noise to disambiguate
  
  % horis prior
  h = mean(horis_prior(SP==i));
  e2 = h*(-hor)+(1-h)*hor;
  
  % disparity prior
  e3 = F_unary(i,:);% + 0.1*rand(1,num_planes); % add noise to disambiguate
  
  factors{k}.v = i;
  factors{k}.e = params.unary.w1*e1 + ...
                 params.unary.w2*e2 + ...
                 params.unary.w3*e3;
  k=k+1;
end

% superpixel-superpixel potentials (pairwise)
for idx=find(SP_adj)'
  [i j] = ind2sub(size(SP_adj),idx);
  factors{k}.v = [i j];
  factors{k}.e = E_pair{i,j}(:)';
  k=k+1;
end

% inference     
if verbose      
  fprintf('Solving CRF ... \n');    
end            
plane_idx = smsMex(variables,factors,10,verbose); 
