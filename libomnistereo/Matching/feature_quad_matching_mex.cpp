#include "mex.h"
#include <iostream>
#include <opencv2/features2d/features2d.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/nonfree/features2d.hpp>
#include <opencv2/nonfree/nonfree.hpp>
#include <math.h>
#include "MatchingQuadSmall.h"

void feature_matching_quad ( int frame_number, char* detectorN, char* descriptorN, char* matchingN, char* seqFolderN, char* seqNameN, char* camName1, char* camName2, char* save_name, char* mask_folderN ) {
     
    // Select Feature Detector / Desriptor and Matching
    std::string detectorName    = std::string(detectorN); 
    std::string descriptorName  = std::string(descriptorN); ;
    std::string MatchingType    = std::string(matchingN);
    std::string seqfolder       = std::string(seqFolderN); 
    std::string seqname         = std::string(seqNameN);
    std::string camname1        = std::string(camName1);
    std::string camname2        = std::string(camName2);
    std::string mask_folder     = std::string(mask_folderN);

    
    char fmL[500], fmR[500], fnL[500], fnR[500], fnB[500], fmB[500], fmL1[500], fmR1[500];

    sprintf(fmL1,"%s/Maske_Left.png",mask_folder.c_str());
    sprintf(fmR1,"%s/Maske_Right.png",mask_folder.c_str());

    

    Mat maske_left  = cvLoadImageM( fmL1, CV_LOAD_IMAGE_GRAYSCALE );
    Mat maske_right = cvLoadImageM( fmR1, CV_LOAD_IMAGE_GRAYSCALE );
    
    std::vector<cv::KeyPoint> keypoints_prev_left_all, keypoints_cur_left_all;
    std::vector<cv::KeyPoint> keypoints_prev_right_all, keypoints_cur_right_all;
    std::vector<cv::KeyPoint> keypoints_prev_back, keypoints_cur_back;
    std::vector<cv::KeyPoint> keypoints_prev_left, keypoints_prev_right;
    std::vector<cv::KeyPoint> keypoints_cur_left, keypoints_cur_right;

    cv::Mat descriptors_prev_left, descriptors_cur_left;
    cv::Mat descriptors_prev_right, descriptors_cur_right;

    cv::initModule_nonfree();

    /* ********************************************************** */
    int q = frame_number;
        
    // load images
        sprintf( fnL, "%s/%s/%s/data/%010d.png", seqfolder.c_str(), seqname.c_str(), camname1.c_str(), q);
        sprintf( fnR, "%s/%s/%s/data/%010d.png", seqfolder.c_str(), seqname.c_str(), camname2.c_str(), q);
    
    Mat prev_left = cvLoadImageM( fnL, CV_LOAD_IMAGE_GRAYSCALE );
    Mat prev_right = cvLoadImageM( fnR, CV_LOAD_IMAGE_GRAYSCALE );

    /* ********************** */
    //-- Step 1: DETECTION -- //
    /* ********************** */
    Ptr<cv::FeatureDetector> detector = FeatureDetector::create(detectorName);
    if (detectorName.compare("FAST") == 0 ) {
        detector->set("threshold", 20);
    }

    detector->detect(prev_left, keypoints_prev_left_all);
    detector->detect(prev_right, keypoints_prev_right_all);


    if (MatchingType.compare("Fisheye")==0)
    {
        keypoints_prev_left = keypoints_prev_left_all;
        keypoints_prev_right = keypoints_prev_right_all;
    } else {
        select_nonvehicle_keypoints ( keypoints_prev_left,  keypoints_prev_left_all,  maske_left);
        select_nonvehicle_keypoints ( keypoints_prev_right, keypoints_prev_right_all, maske_right);
    }
    
    //-- Step 2: Calculate descriptors (feature vectors) -- //
    /* **************************************************** */
    Ptr<DescriptorExtractor> extractor = DescriptorExtractor::create(descriptorName);

    extractor->compute( prev_left, keypoints_prev_left, descriptors_prev_left);
    extractor->compute( prev_right, keypoints_prev_right, descriptors_prev_right);


    // load images
        sprintf( fmL, "%s/%s/%s/data/%010d.png", seqfolder.c_str(), seqname.c_str(), camname1.c_str(), q+1);
        sprintf( fmR, "%s/%s/%s/data/%010d.png", seqfolder.c_str(), seqname.c_str(), camname2.c_str(), q+1);


    Mat cur_left = cvLoadImageM( fmL, CV_LOAD_IMAGE_GRAYSCALE );
    Mat cur_right = cvLoadImageM( fmR, CV_LOAD_IMAGE_GRAYSCALE );


    Mat correspondFeatures; 
    correspondFeatures = Mat ( cvSize(prev_left.cols*2, prev_left.rows + cur_left.rows), CV_8UC3 );
    createCorrespondImage (correspondFeatures, cur_left, prev_left, prev_left, prev_right );
          
    
    /* ********************** */
    //-- Step 1: DETECTION -- //
    /* ********************** */
    detector->detect(cur_left, keypoints_cur_left_all);
    detector->detect(cur_right, keypoints_cur_right_all);

    if (MatchingType.compare("Fisheye")==0)
    {
        keypoints_cur_left = keypoints_cur_left_all;
        keypoints_cur_right = keypoints_cur_right_all;
    } else {
        select_nonvehicle_keypoints ( keypoints_cur_left,   keypoints_cur_left_all,   maske_left);
        select_nonvehicle_keypoints ( keypoints_cur_right,  keypoints_cur_right_all,  maske_right);
    }
            
    /* **************************************************** */
    //-- Step 2: Calculate descriptors (feature vectors) -- //
    /* **************************************************** */
    extractor->compute( cur_left, keypoints_cur_left, descriptors_cur_left);
    extractor->compute(cur_right, keypoints_cur_right, descriptors_cur_right);

    
    /* ******************************** */
    //-- Step 3: Matching descriptor -- //
    /* ******************************** */
     // matches between left and right camera
    std::vector< cv::DMatch > matches_LR_Le_PreCur, matches_LR_Le_CurPre, matches_LR_LeRi_Pre, matches_LR_LeRi_Cur, matches_LR_Ri_PreCur;

    if (MatchingType.compare("Hamming") == 0 ) {
                
        BFMatcher matcher_LR_Le_PreCur( NORM_HAMMING, true);
        BFMatcher matcher_LR_Le_CurPre( NORM_HAMMING, true );
        BFMatcher matcher_LR_LeRi_Pre( NORM_HAMMING, true );
        BFMatcher matcher_LR_LeRi_Cur( NORM_HAMMING, true );
        BFMatcher matcher_LR_Ri_PreCur( NORM_HAMMING, true );
        
        matcher_LR_Le_PreCur.match  (descriptors_prev_left, descriptors_cur_left,   matches_LR_Le_PreCur);
        matcher_LR_Le_CurPre.match  (descriptors_cur_left,  descriptors_prev_left,  matches_LR_Le_CurPre); 
        matcher_LR_LeRi_Cur.match   (descriptors_cur_left,  descriptors_cur_right,  matches_LR_LeRi_Cur);
        matcher_LR_LeRi_Pre.match   (descriptors_prev_left, descriptors_prev_right, matches_LR_LeRi_Pre);
        
        matcher_LR_Ri_PreCur.match  (descriptors_prev_right, descriptors_cur_right, matches_LR_Ri_PreCur);

        matcher_LR_Le_PreCur.clear();
        matcher_LR_Le_CurPre.clear();
        matcher_LR_LeRi_Pre.clear();
        matcher_LR_LeRi_Cur.clear();
        matcher_LR_Ri_PreCur.clear();   

    } else if (MatchingType.compare("L2") == 0 ) {
        
        BFMatcher matcher_LR_Le_PreCur( NORM_L2);
        BFMatcher matcher_LR_Le_CurPre( NORM_L2 );
        BFMatcher matcher_LR_LeRi_Pre( NORM_L2 );
        BFMatcher matcher_LR_LeRi_Cur( NORM_L2 );
        BFMatcher matcher_LR_Ri_PreCur( NORM_L2 );
        
        matcher_LR_Le_PreCur.match  (descriptors_prev_left, descriptors_cur_left,   matches_LR_Le_PreCur);
        matcher_LR_Le_CurPre.match  (descriptors_cur_left,  descriptors_prev_left,  matches_LR_Le_CurPre);
        matcher_LR_LeRi_Pre.match   (descriptors_prev_left, descriptors_prev_right, matches_LR_LeRi_Pre);
        matcher_LR_LeRi_Cur.match   (descriptors_cur_left,  descriptors_cur_right,  matches_LR_LeRi_Cur);
        matcher_LR_Ri_PreCur.match  (descriptors_prev_right, descriptors_cur_right, matches_LR_Ri_PreCur);

        matcher_LR_Le_PreCur.clear();
        matcher_LR_Le_CurPre.clear();
        matcher_LR_LeRi_Pre.clear();
        matcher_LR_LeRi_Cur.clear();
        matcher_LR_Ri_PreCur.clear();
    }

    std::vector< cv::DMatch > good_matches_Le_PreCur, good_matches_Le_CurPre, good_matches_LeRi_Pre, good_matches_LeRi_Cur, good_matches_Ri_PreCur;

    double minDist2 = 3;

    // only for BRIEF no influence for SURF
    calculate_good_matches (good_matches_Le_PreCur,  descriptors_prev_left,     matches_LR_Le_PreCur,   minDist2, false);
    calculate_good_matches (good_matches_Le_CurPre,  descriptors_cur_left,      matches_LR_Le_CurPre,   minDist2, false);
    calculate_good_matches (good_matches_LeRi_Pre,   descriptors_prev_left,     matches_LR_LeRi_Pre,    minDist2, false);
    calculate_good_matches (good_matches_LeRi_Cur,   descriptors_cur_left,      matches_LR_LeRi_Cur,    minDist2, false);
    calculate_good_matches (good_matches_Ri_PreCur,  descriptors_prev_right,    matches_LR_Ri_PreCur,   minDist2, false);

    FILE *KorresPoints;
    char korres_points [500];

    sprintf( korres_points, "%s/KorresPoints_LR_%010d_%010d.txt", save_name, q, q+1);
    KorresPoints = fopen( korres_points, "a");


    
    int matches_fisheye;

    int matches_quad_LeRi = quad_matching_act (good_matches_Le_PreCur, good_matches_Le_CurPre, good_matches_LeRi_Pre, good_matches_Ri_PreCur, good_matches_LeRi_Cur,
            &keypoints_prev_left, &keypoints_cur_left, &keypoints_prev_right, &keypoints_cur_right, 
            correspondFeatures, prev_left, 1, KorresPoints);

    fclose(KorresPoints);


    correspondFeatures.release();

    cur_left.release();
    cur_right.release();

    keypoints_cur_left.clear();
    keypoints_cur_right.clear();
    keypoints_cur_left_all.clear();
    keypoints_cur_right_all.clear();
    keypoints_cur_back.clear();

    descriptors_cur_left.release();
    descriptors_cur_right.release();

    matches_LR_Le_PreCur.clear();
    matches_LR_Le_CurPre.clear();
    matches_LR_LeRi_Pre.clear();
    matches_LR_LeRi_Cur.clear();
    matches_LR_Ri_PreCur.clear();

    good_matches_Le_PreCur.clear();
    good_matches_Le_CurPre.clear();
    good_matches_LeRi_Pre.clear();
    good_matches_LeRi_Cur.clear();
    good_matches_Ri_PreCur.clear();

    prev_left.release();
    prev_right.release();

    keypoints_prev_left.clear();
    keypoints_prev_right.clear();
    keypoints_prev_left_all.clear();
    keypoints_prev_right_all.clear();
    keypoints_prev_back.clear();

    descriptors_prev_left.release();
    descriptors_prev_right.release();

    detector.release();
    extractor.release();

    maske_left.release();
    maske_right.release();

}


void mexFunction (int nlhs,mxArray *plhs[],int nrhs,const mxArray *prhs[]) {
    
    // check arguments
    if (nrhs!=10)
      mexErrMsgTxt("10 inputs and required (frame_number, detector, descriptor, matching, seqFolder, seqName, camName1, camName2, saveName,maskFolder).");
    
    double* frame_number = (double*)mxGetPr(prhs[0]);
    //int *frame_number = (int *) mxGetData(prhs[0]);
       
    char *detector;
    char *descriptor;
    char *matchingtype;
    char *seqFolder;
    char *seqName;
    char *camName1;
    char *camName2;
    char *saveName;
    char *maskFolder;

    int   n;
    int   status;

//     std::cout << *frame_number << std::endl;
            
    n = (mxGetM(prhs[1]) * mxGetN(prhs[1])) + 1;
    detector = (char*)mxCalloc(n, sizeof(char));

    status = mxGetString(prhs[1], detector, n); 
//     if (status == 0)
//         mexPrintf("The converted Detector is \n%s.\n", detector);
//     else
//         mexErrMsgTxt("Could not convert string data.");
    
    n = (mxGetM(prhs[2]) * mxGetN(prhs[2])) + 1;
    descriptor = (char*)mxCalloc(n, sizeof(char));
    
    status = mxGetString(prhs[2], descriptor, n); 
//     if (status == 0)
//         mexPrintf("The converted Descriptor is \n%s.\n", descriptor);
//     else
//         mexErrMsgTxt("Could not convert string data.");
    
    n = (mxGetM(prhs[3]) * mxGetN(prhs[3])) + 1;
    matchingtype = (char*)mxCalloc(n, sizeof(char));
    
    status = mxGetString(prhs[3], matchingtype, n); 
//     if (status == 0)
//         mexPrintf("The converted MatchingType is \n%s.\n", matchingtype);
//     else
//         mexErrMsgTxt("Could not convert string data.");
    
    n = (mxGetM(prhs[4]) * mxGetN(prhs[4])) + 1;
    seqFolder = (char*)mxCalloc(n, sizeof(char));
    
    status = mxGetString(prhs[4], seqFolder, n); 
//     if (status == 0)
//         mexPrintf("The converted seqFolder is \n%s.\n", seqFolder);
//     else
//         mexErrMsgTxt("Could not convert string data.");
    
    n = (mxGetM(prhs[5]) * mxGetN(prhs[5])) + 1;
    seqName = (char*)mxCalloc(n, sizeof(char));
    
    status = mxGetString(prhs[5], seqName, n); 
//     if (status == 0)
//         mexPrintf("The converted seqName is \n%s.\n", seqName);
//     else
//         mexErrMsgTxt("Could not convert string data.");
    
    n = (mxGetM(prhs[6]) * mxGetN(prhs[6])) + 1;
    camName1 = (char*)mxCalloc(n, sizeof(char));
    
    status = mxGetString(prhs[6], camName1, n); 
//     if (status == 0)
//         mexPrintf("The converted camName1 is \n%s.\n", camName1);
//     else
//         mexErrMsgTxt("Could not convert string data.");
    
    n = (mxGetM(prhs[7]) * mxGetN(prhs[7])) + 1;
    camName2 = (char*)mxCalloc(n, sizeof(char));
    
    status = mxGetString(prhs[7], camName2, n); 
//     if (status == 0)
//         mexPrintf("The converted camName2 is \n%s.\n", camName2);
//     else
//         mexErrMsgTxt("Could not convert string data.");
    
    n = (mxGetM(prhs[8]) * mxGetN(prhs[8])) + 1;
    saveName = (char*)mxCalloc(n, sizeof(char));
    
    status = mxGetString(prhs[8], saveName, n); 
    
    n = (mxGetM(prhs[9]) * mxGetN(prhs[9])) + 1;
    maskFolder = (char*)mxCalloc(n, sizeof(char));
    
    status = mxGetString(prhs[9], maskFolder, n); 

    feature_matching_quad ( *frame_number, detector, descriptor, matchingtype, seqFolder, seqName, camName1, camName2, saveName, maskFolder );   
        
}
