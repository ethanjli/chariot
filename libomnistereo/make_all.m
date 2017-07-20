opts = init;

% path for the first make file
p = [opts.root_dir,'/src'];

% make quadmatching
path = [p, '/Matching'];    
cd(path);
make_quadmatching;

path = [p, '/Mapping'];
cd(path);
make;

path = [path, '/Centered_Model'];
cd(path);
make;

path = [p, '/Rectification'];
cd(path)
make;

path = [p, '/Reconstruction'];
cd(path)
make;

% make mex RoadPlane
path = [path, '/PlaneEstimation/RoadPlane'];
cd(path)
make;

% make mex MRF
path = [p, '/Reconstruction/PlaneEstimation/MRF'];
cd(path)
make;

% make mex sms
path = [path,'/sms'];
cd(path)
make;

% make superpixel
% path = [p, '/Superpixel'];
% cd(path);
% make;

cd(p);
