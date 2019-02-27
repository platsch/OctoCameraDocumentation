# -*- coding: utf-8 -*-

""" This file is part of OctoCameraDocumentation
    
    This is a test script to execute the imageprocessing-steps independent from the main software
    and particularly without a running printer.
   
    Main author: Florens Wasserfall <wasserfall@kalanka.de>
"""

import ImageAnalyzer
import GCodeProcessor
import GridGenerator
import time
import os
import cv2
import numpy as np
import csv
from sklearn.svm import LinearSVC
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

base_path = "testimages/conductive"
gcode_file = "cube_wires.gcode"
layer = 3

gcode_file = os.path.join(base_path, gcode_file)
image_file = os.path.join(base_path, 'Layer_{}'.format(layer) + '_result.png')
positive_mask_file = os.path.join(base_path, 'Layer_{}'.format(layer) + '_result_positive_mask.png')
negative_mask_file = os.path.join(base_path, 'Layer_{}'.format(layer) + '_result_negative_mask.png')
labeled_file = os.path.join(base_path, 'Layer_{}'.format(layer) + '_result_labeled_pixels.png')
result_highlight_file = os.path.join(base_path, 'Layer_{}'.format(layer) + '_result_highlighted.png')



# import gcode file
gcode = open(gcode_file, 'r')
readData = gcode.readlines()
gcode.close()
gcode_processor = GCodeProcessor.GCodeProcessor(readData, max_extruder_num = 1)
gcode_list = gcode_processor.gcodePerLayer()

grid_maker = GridGenerator.CameraGridMaker(gcode_list,layer,14.76015,14.76015)
grid = grid_maker.getCameraCoords()

# open image
image = cv2.imread(image_file)

start_time = time.time()

ia = ImageAnalyzer.ImageAnalyzer(gcode_list[layer], image, 54.2, 54.3, grid_maker.getMinX(), grid_maker.getMinY(), grid_maker.getMaxX(), grid_maker.getMaxY())
mask = ia.extruder_mask(extruder_num = 1, extrusion_width = 0.6)

negative_mask = cv2.bitwise_and(image, image, mask=mask)
cv2.imwrite(negative_mask_file, negative_mask)

inverse_mask = 255 - mask
positive_mask = cv2.bitwise_or(image, image, mask=inverse_mask)
cv2.imwrite(positive_mask_file, positive_mask)

label_img = ia.mark_extruder_pixels(extruder_num = 1, max_extruder_num = 1, extrusion_width = 0.5)

# search for defects
result, highlighted_image = ia.traverse_gcode(label_img, image, extruder_num = 1, extrusion_width = 0.6)

cv2.imwrite(result_highlight_file, highlighted_image)
cv2.imwrite(labeled_file, label_img)


end_time = time.time();
print("--- %s seconds ---" % (time.time() - start_time))
