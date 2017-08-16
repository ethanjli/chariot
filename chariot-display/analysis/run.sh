#!/bin/bash

HOME_DIR=`pwd`
MATLAB_DIR="$HOME_DIR/matlab"
LOG_DIR="$HOME_DIR/logs"

#DATA
RECORD='/home/tj/Data/VideoPopup'
R_INPUT="$RECORD/Input"
R_MOTSEG="$RECORD/Motseg"
R_RECON="$RECORD/DepthReconstruction"

CVFISH='/home/cvfish/Work/code/bitbucket/video_popup'
BROX_MALIK="$CVFISH/data/Log_C920_x1/3"
CODE=$CVFISH
INPUT="$BROX_MALIK/5_images"


size=4

#Make sure the matlab/python is correct 
alias matlab="LD_PRELOAD=\"/usr/lib/x86_64-linux-gnu/libstdc++.so.6:$LD_PRELOAD\" /usr/local/MATLAB/R2013a/bin/matlab"
alias python="/usr/bin/python"

#Create a directory in RECORD/INPUT and store surf points for each image in INPUT, save to file
mkdir $R_INPUT
cd $R_INPUT
for i in `ls $INPUT`; do
	matlab -nodisplay -r "addpath $MATLAB_DIR; try, find_features('$INPUT/$i', 100  ), catch ME, getReport(ME), end ; exit"
done
cd $HOME_DIR

#Run the original broxMalik sh file in BROX_MALIK
cd $BROX_MALIK
bash runBroxMalik_${size}.sh 1>$LOG_DIR/br_logs.txt 2>$LOG_DIR/br_err.txt
cd $HOME_DIR

#####Adding variables for the second part of the script

tracks=`ls ${INPUT} | wc -l`
BM_RESULTS="$BROX_MALIK/broxmalik_Size${size}/broxmalikResults/broxmalikTracks${tracks}.dat"
MOTSEG_RESULTS="$BROX_MALIK/broxmalik_Size${size}/broxmalikResults/f1t${tracks}/v1/vw10_nn10_k1_thresh100_max_occ2_op0_cw2.5/init200/mdl20000_pw3000_oc10_engine0_it5"

######################################################################

#Run motion segmentation in CODE directory, pass in the DATA
cd $CODE
python -m video_popup.motion_segmentation.video_popup_motseg  --images_dir $INPUT --tracks_path $BM_RESULTS 1>$LOG_DIR/motseg_logs.txt 2>$LOG_DIR/motseg_err.txt
cd $HOME_DIR

#####MOTSEG RESULTS


#Create a directory to take the .mat file in RESULTS and display the segmentation, store in MOTSEG directory
mkdir $R_MOTSEG
cd $R_MOTSEG
cp $MOTSEG_RESULTS/results.mat .
matlab -nodisplay -r "addpath $MATLAB_DIR; addpath $R_MOTSEG; try,  load results.mat; save_segmentation('results.mat'), catch ME, getReport(ME), end; exit"
cd $HOME_DIR

##########################
#Run depth reconstruction in CODE
cd $CODE
python -m video_popup.depth_reconstruction.depth_reconstruction_test --seg_file $MOTSEG_RESULTS/results.pkl 1>$LOG_DIR/recon_logs.txt 2>$LOG_DIR/recon_err.txt
cd $HOME_DIR

#Make directory RECON in in RECORD, Move pointcloud in RESULTS/SuperPixels and move into RECON, categorize into each type
mkdir $R_RECON
cd $R_RECON
cp $MOTSEG_RESULTS/SparseResults/results.mat $R_RECON

#Add the point cloud data
mkdir pc
cd pc
mkdir Sparse
cp $MOTSEG_RESULTS/SuperPixels/points_sparse* Sparse
mkdir DenseLinear
cp $MOTSEG_RESULTS/SuperPixels/points_dense_linear* DenseLinear
mkdir DenseForeground
cp $MOTSEG_RESULTS/SuperPixels/points_dense_foreground* DenseForeground


#Move results in RESULTS/SparseResults, move into RECON, store depth images into depth images directory.

cd $HOME_DIR
