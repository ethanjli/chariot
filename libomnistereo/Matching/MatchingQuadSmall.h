#ifndef MATCHING_H
#define MATCHING_H

#include "opencv2/core/core.hpp"
#include "opencv2/features2d/features2d.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/calib3d/calib3d.hpp"
#include <opencv2/imgproc/imgproc.hpp>
#include <iostream>
#include <vector>
#include <fstream>

using namespace std;
using namespace cv;

void createCorrespondImage (Mat &correspond, Mat &img1, Mat &img2, Mat &img3, Mat &img4);

void select_nonvehicle_keypoints ( vector<KeyPoint> &keypoints_new, vector<KeyPoint> keypoints, Mat maske);

int quad_matching_act (vector<DMatch> ptpairs_12, vector<DMatch> ptpairs_21, vector<DMatch> ptpairs_13, vector<DMatch>  ptpairs_34, vector<DMatch>  ptpairs_24,
                   vector<KeyPoint> *Keypoints_1, vector<KeyPoint> *Keypoints_2, vector<KeyPoint> *Keypoints_3, vector<KeyPoint> *Keypoints_4,
                       Mat &correspond, Mat &object_left, int matcherImg, FILE *KorresPoints ); //char save_name[500]

void calculate_good_matches (vector<DMatch> &good_matches, Mat descriptors, vector<DMatch> matches,double &mindist, bool calc_minDist);

void locateImagePoints ( vector<Point2f> &firstPoint, vector<Point2f> &secPoint, vector<KeyPoint> firstKey, vector<KeyPoint> secKey, vector<DMatch> good_matches);

#endif // MATCHING_H
