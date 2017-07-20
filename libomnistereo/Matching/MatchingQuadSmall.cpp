#include "MatchingQuadSmall.h"
#include <vector>

void createCorrespondImage (Mat &correspond, Mat &img1, Mat &img2, Mat &img3, Mat &img4)
{
    // ************************** //
    // ***  1   ******   3    *** //
    // ************************** //
    // ***  2   ******   4    *** //
    // ************************** //

    int diffWidth = img1.cols - img2.cols;

    Mat img1_color = Mat ( img1.size(), 8, 3);
    cvtColor( img1, img1_color, CV_GRAY2BGR );
    Mat img2_color = Mat (img2.size(), 8, 3);
    cvtColor( img2, img2_color, CV_GRAY2BGR );
    Mat img3_color = Mat (img3.size(), 8, 3);
    cvtColor( img3, img3_color, CV_GRAY2BGR );
    Mat img4_color = Mat (img4.size(), 8, 3);
    cvtColor( img4, img4_color, CV_GRAY2BGR );

    // show correspondences only in the left images also for stereo
    if (diffWidth >= 0) {
        //correspond = cvCreateImage( cvSize(img1->width*2, img1->height+img2->height), 8, 3 );

        //cvSetImageROI( correspond, cvRect( 0, 0, img1.cols, img1.rows ) );
        //cvCopy( img1_color, correspond(0, 0, img1.cols, img1.rows) );
        Mat roi = correspond(Rect(0,0,img1_color.cols,img1_color.rows));
        img1_color.copyTo( roi );

//        cvSetImageROI( correspond, cvRect( 0, img1.rows, img2.cols, correspond->height ) );
//        cvCopy( img2_color, correspond );
        roi = correspond(Rect(0,img1.rows,img2.cols,img2.rows));
        img2_color.copyTo( roi );

        //cvSetImageROI( correspond, cvRect( img1.cols, 0, correspond->width, img1.rows) );
        //cvCopy( img3_color, correspond );
        roi = correspond(Rect(img1.cols,0,img1.cols,img1.rows));
        img3_color.copyTo( roi );

//        cvSetImageROI( correspond, cvRect( img1.cols, img1.rows, img2.cols , correspond->height ) );
//        cvCopy( img4_color, correspond );
        roi = correspond(Rect(img1.cols,img1.rows,img2.cols,img2.rows));
        img4_color.copyTo( roi );
//
        roi.release();
    }

    img1_color.release();
    img2_color.release();
    img3_color.release();
    img4_color.release();

}

void select_nonvehicle_keypoints ( vector<KeyPoint> &keypoints_new, vector<KeyPoint> keypoints, Mat maske ) {

    int ind = 0;
    for (int i = 1; i < keypoints.size(); i++) {

        int test = maske.at<uchar>(keypoints[i].pt.y, keypoints[i].pt.x ) ;

        if (test == 255) {
            keypoints_new.push_back(keypoints[i]);
            ind = ind + 1;
           
        }

    }
}


int quad_matching_act (vector<DMatch> ptpairs_12, vector<DMatch> ptpairs_21, vector<DMatch> ptpairs_13, vector<DMatch>  ptpairs_34, vector<DMatch>  ptpairs_24,
                   vector<KeyPoint> *Keypoints_1, vector<KeyPoint> *Keypoints_2, vector<KeyPoint> *Keypoints_3, vector<KeyPoint> *Keypoints_4,
                       Mat &correspond, Mat &object_left, int matcherImg, FILE *KorresPoints)

{

    //-- Localize the object
    vector<Point2f> Pairs_12_1, Pairs_12_2, Pairs_13_1, Pairs_13_3, Pairs_34_3, Pairs_34_4, Pairs_24_2, Pairs_24_4, Pairs_21_1, Pairs_21_2;

    // ptpairs = Matching between previous and current image
    locateImagePoints ( Pairs_12_1, Pairs_12_2, *Keypoints_1, *Keypoints_2, ptpairs_12); //Matching Object Image
    locateImagePoints ( Pairs_21_2, Pairs_21_1, *Keypoints_2, *Keypoints_1, ptpairs_21);
    locateImagePoints ( Pairs_13_1, Pairs_13_3, *Keypoints_1, *Keypoints_3, ptpairs_13);  // Matching Image Object
    locateImagePoints ( Pairs_34_3, Pairs_34_4, *Keypoints_3, *Keypoints_4, ptpairs_34);
    locateImagePoints ( Pairs_24_2, Pairs_24_4, *Keypoints_2, *Keypoints_4, ptpairs_24);
    
    int matches = 0;
    int matches_12_21 = 0; int matches_12_13 = 0; int matches_13_34=0;
    bool counterV;
    
    for (int i=0; i<Pairs_12_1.size(); i++)								//Var I for Left
    {
        counterV = false;
                for (int k=0; k< Pairs_13_1.size(); k++)
                {
                    if (counterV) {break; }
                    else if ( (Pairs_12_1[i] == Pairs_13_1[k]) )
                    {
                        matches_12_13++;
                        for (int j=0; j < (int)Pairs_34_3.size(); j++)							//Var J for First
                        {
                            if (counterV) { break; }
                            else if (Pairs_13_3[k] == Pairs_34_3[j])
                            {
                                matches_13_34++;

                                        if ( abs(Pairs_13_1[k].x - Pairs_13_3[k].x) <=100  && abs(Pairs_13_1[k].y - Pairs_13_3[k].y) <=100 && //abs(Pairs_24_2[n].x - Pairs_24_4[n].x) <=100  && abs(Pairs_24_2[n].y - Pairs_24_4[n].y) <=100 &&
                                             abs(Pairs_12_1[i].x - Pairs_12_2[i].x) <=100  && abs(Pairs_12_1[i].y - Pairs_12_2[i].y) <=100) {

                                            matches++;

                                            fprintf(KorresPoints,"%lf %lf %lf %lf %lf %lf %lf %lf\n", Pairs_12_1[i].x, Pairs_12_1[i].y, Pairs_13_3[k].x, Pairs_13_3[k].y,
                                                   Pairs_12_2[i].x, Pairs_12_2[i].y, Pairs_34_4[j].x, Pairs_34_4[j].y);
                                        }

                            }
                            else if (j == (int)Pairs_34_3.size()-1)
                            {
                                counterV = true;
                                break;
                            }
                        }
                    }
                    else if (k == ((int)Pairs_13_1.size()-1))
                    {
                        break;
                    }
              }
    }

    return matches;
}


void calculate_good_matches (vector<DMatch> &good_matches, Mat descriptors, vector<DMatch> matches, double &mindist, bool calc_minDist)
{
    double max_dist = 0; double min_dist = 100;
    if (calc_minDist) {

        //-- Quick calculation of max and min distances between keypoints
        for( int i = 0; i < descriptors.rows; i++ )
        { double dist = matches[i].distance;
        if( dist < min_dist ) min_dist = dist;
        if( dist > max_dist ) max_dist = dist;
        }
        mindist = min_dist;
    } else {
        min_dist = mindist;
    }

    for (int i = 0; i < matches.size(); i++)
    { 
        if( matches[i].distance <= 12*min_dist )
        { 
            good_matches.push_back( matches[i]); 
        }
    }

}


void locateImagePoints ( vector<Point2f> &firstPoint, vector<Point2f> &secPoint, vector<KeyPoint> firstKey, vector<KeyPoint> secKey, vector<DMatch> good_matches)
{   
    for( int i = 0; i < good_matches.size(); i++ )
    {
        //if ( good_matches[i].distance == 0 ) {
            //-- Get the keypoints from the good matches
        firstPoint.push_back( firstKey[ good_matches[i].queryIdx ].pt );
        secPoint.push_back( secKey[ good_matches[i].trainIdx ].pt );
            
            
        //}
      }
         
}



