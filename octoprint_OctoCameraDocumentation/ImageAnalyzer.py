'''
Created on 22.02.2018
@author: Florens Wasserfall

'''

import re
import cv2
import numpy as np


class ImageAnalyzer:

    gcode = None
    image = None
    pixel_per_mm_x = 10
    pixel_per_mm_y = 10
    offset_x = 0
    offset_y = 0

    def __init__(self, layerGCode, image, pixel_per_mm_x, pixel_per_mm_y, min_x, min_y, max_x, max_y):
        self.gcode = layerGCode
        self.image = image
        self.pixel_per_mm_x = pixel_per_mm_x
        self.pixel_per_mm_y = pixel_per_mm_y
        range_x = max_x - min_x
        range_y = max_y - min_y
        self.offset_x = min_x*pixel_per_mm_x - (image.shape[1] - range_x*pixel_per_mm_x) / 2
        self.offset_y = min_y*pixel_per_mm_y - (image.shape[0] - range_y*pixel_per_mm_y) / 2

    def extruder_pixels(self, extruder_num, extrusion_width, HSV = False, limit = 0):
        mask = self.extruder_mask(extruder_num, extrusion_width)
        image = self.image
        if(HSV):
            print "converting to HSV!"
            image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        templated = cv2.bitwise_and(image, image, mask=mask)

        # extract list of pixels from masked image
        #cond = np.not_equal(templated, [0, 0, 0])
        i = 0
        result = []
        #for row in range(templated.shape[0]):
        #    for col in range(templated.shape[1]):
        #        if((templated.shape[row][col] != np.array([0, 0, 0])).all()):
        #            result.append(templated.shape[row][col])
                #if(templated.item(row, col) != np.array([0, 0, 0]).all()):
                #    result.append(templated.item(col, row))
        #        if(cond[row][col][0] != cond[row][col][1]):
        #            print templated[row][col]


        #print cond
        #result = np.extract(cond, templated)
        #print len(result)
        #result = np.reshape(result, (len(result)/3, 3))
        result = templated[np.any(templated != [0, 0, 0], axis=-1)]


        
        #for col in templated:
        #    for pixel in col:
        #        if((pixel != np.array([0, 0, 0])).all()):
        #            result.append(pixel)
        #    if(len(result) > 3*limit) and limit > 0:
        #        break
        
        if(limit == 0):
            limit = len(result)
        return result[0:limit]

    def extruder_mask(self, extruder_num, extrusion_width):
        extrusion_width = int(extrusion_width * ((self.pixel_per_mm_x + self.pixel_per_mm_y) / 2))
        if(len(self.gcode[extruder_num]) > 1):
            mask = np.zeros((self.image.shape[0], self.image.shape[1]), np.uint8)
            #mask[:, :] = 255

            for g in self.gcode[extruder_num]:
                cv2.line(mask, self._translate(g.a.x, g.a.y), self._translate(g.b.x, g.b.y), 255, extrusion_width, 8)

            #cv2.imshow("mask", mask)
            #cv2.waitKey(0)

        return mask
    
    def _translate(self, x, y):
        return (int(x*self.pixel_per_mm_x - self.offset_x), 
            self.image.shape[0] - int(y*self.pixel_per_mm_y - self.offset_y))