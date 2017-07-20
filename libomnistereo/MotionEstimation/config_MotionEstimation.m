%% conifg_MotionEstimation
%% Parameter for motion estimation


me.calib_initial  = 3;   % Calibration Method for the initialization (at the moment only (1)
me.calib = 14;           % Calibration Method number for the ransac and complete


me.saveEveryFrame_on = 0;
me.estimation3D_on = 1;                                                     


me.options=optimset('Algorithm','levenberg-marquardt', 'Display','off',... 
                 'TolX',1e-4, 'TolFun',1e-4, ...
                 'DerivativeCheck','off', 'Diagnostics','off', ...
                 'Jacobian','off', ...
                 'ScaleProblem', 'Jacobian',...
                 'JacobPattern','sparse(ones(Jrows,Jcols))',...
                 'MaxFunEvals', 247*1000, ...
                 'MaxIter',100);
             
nums_ran = 50;