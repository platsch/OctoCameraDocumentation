'''
Created on 21.02.2019.
@author: Florens Wasserfall
'''

import cv2
import numpy as np

class ImageStitcher:

    rows = 0
    cols = 0
    overlap = 0
    images = []

    def __init__(self, rows, cols, overlap, images):
        self.rows = rows
        self.cols = cols
        self.overlap = overlap
        self.images = images

    def merge_trivial(self):
        result = None
        if(len(self.images) > 0):
            shape_x = self.images[0].shape[1] - 2*self.overlap
            shape_y = self.images[0].shape[0] - 2*self.overlap
            result = np.zeros((shape_y*self.rows, shape_x*self.cols, 3), np.uint8)

            i = 0
            for row in reversed(range(self.rows)): # Y direction in printer is invers to numpy...
                for col in range(self.cols):
                    result[row*shape_y:row*shape_y+shape_y, col*shape_x:col*shape_x+shape_x] = self.images[i][self.overlap:shape_y+self.overlap, self.overlap:shape_x+self.overlap]
                    i+=1

        return result

    def merge_overlapping(self):
        pass

    # img1 is left or top image.
    # max overlap in pixel
    # orientation: 0 = vertical, 1 = horizontal
    def _register_images(img1, img2, max_overlap = 20, orientation = 0, debug = False):
        # Convert images to grayscale
        img1_gray = cv2.cvtColor(im1,cv2.COLOR_BGR2GRAY)
        img2_gray = cv2.cvtColor(im2,cv2.COLOR_BGR2GRAY)
        img1_crop = None;
        img2_crop = None;

        if(orientation):
            # horizontal case, img1 left, img2 right
            img1_crop = img1_gray[0:img1_gray.shape[0], img1_gray.shape[1]-max_overlap:img1_gray.shape[1]]
            img2_crop = img2_gray[0:img2_gray.shape[0], 0:max_overlap]
            if(debug):
                cv2.imshow("Left", img1_crop)
                cv2.imshow("Right", img2_crop)
                cv2.waitKey(0)
        else:
            # vertical case, img1 top, img2 bottom
            img1_crop = img1_gray[img1_gray.shape[0]-max_overlap:img1_gray.shape[0], 0:img1_gray.shape[1]]
            img2_crop = img2_gray[0:max_overlap, 0:img2_gray.shape[1]]
            if(debug):
                cv2.imshow("Top", img1_crop)
                cv2.imshow("Bottom", img2_crop)
                cv2.waitKey(0)
            
         
        # Define 2x3 matirx and initialize the matrix to identity
        warp_matrix = np.eye(2, 3, dtype=np.float32)
         
        # Specify the number of iterations.
        number_of_iterations = 500;
         
        # Specify the threshold of the increment
        # in the correlation coefficient between two iterations
        termination_eps = 1e-10;
         
        # Define termination criteria
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, number_of_iterations,  termination_eps)
         
        # Run the ECC algorithm. The results are stored in warp_matrix.
        (cc, warp_matrix) = cv2.findTransformECC (img1_crop,img2_crop,warp_matrix, cv2.MOTION_TRANSLATION, criteria)

        print "cc: " + str(cc)
        print "warp_matrix: "
        print warp_matrix

        offset_x = -warp_matrix[0, 2]
        offset_y = -warp_matrix[1, 2]

        return (int(round(offset_x)), int(round(offset_y)))
    

"""
# Read the images to be aligned
#im1 =  cv2.imread("images/testset_840px/bl.png");
#im2 =  cv2.imread("images/testset_840px/bc.png");

im1 =  cv2.imread("images/testset_840px/tr_crop.png");
im2 =  cv2.imread("images/testset_840px/br.png");

orientation = 0; # 1: left->right, 0: top->bottom
intersection = 40;

offset_x, offset_y = register_images(im1, im2, max_overlap=intersection, orientation=orientation);

result = np.zeros((im1.shape[0]+im2.shape[0]+2*abs(offset_y),im1.shape[1]+im2.shape[1]+2*abs(offset_x),3), np.uint8)
 
if(orientation):
    # horizontal
    offset_x = intersection - offset_x
    print "offset_x: " + str(offset_x)
    # copy 1. image to result
    result[abs(offset_y):im1.shape[0]+abs(offset_y), 0:im1.shape[1]] = im1
    result[abs(offset_y)+offset_y:abs(offset_y)+offset_y+im2.shape[0] , im1.shape[1]:im1.shape[1]+im2.shape[1]-offset_x] = im2[: , offset_x:im2.shape[1]]
else:
    # vertical
    offset_y = intersection - offset_y
    print "offset_y: " + str(offset_y)
    result[0:im1.shape[0], abs(offset_x):im1.shape[1]+abs(offset_x)] = im1
    result[im1.shape[0]:im1.shape[0]+im2.shape[0]-offset_y, abs(offset_x)+offset_x:abs(offset_x)+offset_x+im2.shape[1]] = im2[offset_y:im2.shape[0], :]


#cv2.imshow("result", result)
 
# Use warpAffine for Translation, Euclidean and Affine
# can we use this for sub-pixel alignment????
#im2_aligned = cv2.warpAffine(im2, warp_matrix, (sz[1],sz[0]), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP);

cv2.imwrite("result.png" ,result)

cv2.waitKey(0)
"""