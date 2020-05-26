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

    def merge_stitching(self):
        result = None
        if(self.overlap < 1):
            result = self.merge_trivial()
        else:
            if(len(self.images) > 0):
                shape_x = self.images[0].shape[1] - 2*self.overlap
                shape_y = self.images[0].shape[0] - 2*self.overlap
                result = np.zeros((shape_y*self.rows, shape_x*self.cols, 3), np.uint8)

                # position of tiles relative to resulting image
                positions = []
                for i in range(self.cols*self.rows):
                    positions.append([0, 0])

                i = 0
                for row in reversed(range(self.rows)): # Y direction in printer is invers to numpy...
                    #line = result = np.zeros((shape_y + 2*self.overlap, shape_x*self.cols, 3), np.uint8)
                    for col in range(self.cols):
                        #result[row*shape_y:row*shape_y+shape_y, col*shape_x:col*shape_x+shape_x] = self.images[i][self.overlap:shape_y+self.overlap, self.overlap:shape_x+self.overlap]
                        offset_x = 0
                        offset_y = 0
                        h_offset_x = 0
                        h_offset_y = 0
                        v_offset_x = 0
                        v_offset_y = 0
                        reg_h = False
                        reg_v = False
                        cc_h = 0
                        cc_v = 0


                        # match against left image
                        print("col: " + str(col) + " row: " + str(row))
                        if(col > 0):
                            reg_h, cc_h, h_offset_x, h_offset_y = self._register_images(self.images[i-1], self.images[i], 2*self.overlap, 1, False)
                            if(cc_h < 0.5): # confidence to low, don't use this value
                                reg_h = False

                        # match against lower image
                        if(row < self.rows-1):
                            reg_v, cc_v, v_offset_x, v_offset_y = self._register_images(self.images[i-self.cols], self.images[i], 2*self.overlap, 0, False)
                            if(cc_v < 0.5): # confidence to low, don't use this value
                                reg_v = False

                        # weighed average of both offsets
                        if(reg_h and reg_v and cc_h > 0.5 and cc_v > 0.5):
                            cc_h = (cc_h - 0.5)*2 # only use [0.5:1.0]
                            cc_v = (cc_v - 0.5)*2
                            w_h = cc_h / (cc_h + cc_v)
                            w_v = cc_v / (cc_h + cc_v)

                            h_offset_x += positions[i-1][0]
                            h_offset_y += positions[i-1][1]
                            v_offset_x += positions[i-self.cols][0]
                            v_offset_x += positions[i-self.cols][1]


                            h_offset_x *= w_h
                            h_offset_y *= w_h
                            v_offset_x *= w_v
                            v_offset_y *= w_v

                            offset_x = int(round(h_offset_x + v_offset_x))
                            offset_y = int(round(h_offset_y + v_offset_y))
                        elif(not reg_v and reg_h): # only horizontal available
                            offset_x = h_offset_x + positions[i-1][0]
                            offset_y = h_offset_y + positions[i-1][1]
                        elif(not reg_h): # only horizontal available
                            offset_x = v_offset_x + positions[i-self.cols][0]
                            offset_y = v_offset_y + positions[i-self.cols][1]

                        # limit offset to overlap...
                        offset_x = max(-self.overlap, min(self.overlap, offset_x))
                        offset_y = max(-self.overlap, min(self.overlap, offset_y))
                        #print "offset_x: " + str(offset_x)
                        #print "offset_y: " + str(offset_x)

                        positions[i] = [offset_x, offset_y]

                        # copy tile into image
                        result[row*shape_y:row*shape_y+shape_y, col*shape_x:col*shape_x+shape_x] = self.images[i][self.overlap-offset_y:shape_y+self.overlap-offset_y, self.overlap-offset_x:shape_x+self.overlap-offset_x]

                        i+=1
        return result


    # img1 is left or top image.
    # max overlap in pixel
    # orientation: 0 = vertical, 1 = horizontal
    def _register_images(self, img1, img2, max_overlap = 20, orientation = 0, debug = False):
        result = True
        img1_crop = None;
        img2_crop = None;

        if(orientation):
            # horizontal case, img1 left, img2 right
            img1_crop = img1[0:img1.shape[0], img1.shape[1]-max_overlap:img1.shape[1]]
            img2_crop = img2[0:img2.shape[0], 0:max_overlap]
            if(debug):
                cv2.imshow("Left", img1_crop)
                cv2.imshow("Right", img2_crop)
                cv2.waitKey(0)
        else:
            # vertical case, img1 bottom, img2 top
            img1_crop = img1[0:max_overlap, 0:img1.shape[1]]
            img2_crop = img2[img2.shape[0]-max_overlap:img2.shape[0], 0:img2.shape[1]]
            if(debug):
                cv2.imshow("Top", img1_crop)
                cv2.imshow("Bottom", img2_crop)
                cv2.waitKey(0)

        # Convert images to grayscale
        img1_gray = cv2.cvtColor(img1_crop,cv2.COLOR_BGR2GRAY)
        img2_gray = cv2.cvtColor(img2_crop,cv2.COLOR_BGR2GRAY)

        # histogram equalization - this should only be applied if backround pixels are masked out to avoid correlation of
        # features from previous layers which are still in the image
        #img1_gray = cv2.equalizeHist(img1_gray)
        #img2_gray = cv2.equalizeHist(img2_gray)
            
         
        # Define 2x3 matirx and initialize the matrix to identity
        warp_matrix = np.eye(2, 3, dtype=np.float32)
         
        # Specify the number of iterations.
        number_of_iterations = 500;
         
        # Specify the threshold of the increment
        # in the correlation coefficient between two iterations
        #termination_eps = 1e-10;
        termination_eps = 1e-8;
         
        # Define termination criteria
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, number_of_iterations,  termination_eps)
         
        # Run the ECC algorithm. The results are stored in warp_matrix.
        offset_x = 0
        offset_y = 0
        cc = 0
        try:
            (cc, warp_matrix) = cv2.findTransformECC (img1_gray,img2_gray,warp_matrix, cv2.MOTION_TRANSLATION, criteria)
            #print "cc: " + str(cc)
            #print "warp_matrix: "
            #print warp_matrix

            offset_x = -warp_matrix[0, 2]
            offset_y = -warp_matrix[1, 2]
        except cv2.error as e:
            #cv2.imshow("img1", img1_crop)
            #cv2.imshow("img2", img2_crop)
            #cv2.waitKey(0)
            #print e
            result = False


        return (result, cc, int(round(offset_x)), int(round(offset_y)))