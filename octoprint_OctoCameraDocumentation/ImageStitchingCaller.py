# -*- coding: utf-8 -*-

""" This file is part of OctoCameraDocumentation
    
    This is a test script to execute the imageprocessing-steps independent from the main software
    and particularly without a running printer.
   
    Main author: Florens Wasserfall <wasserfall@kalanka.de>
"""

import ImageStitcher
import time
import os
import cv2
import numpy as np

base_path = "testimages"
layer = 3
rows = 4
cols = 4
overlap = 40

start_time = time.time()
image_list = []
for i in range(rows*cols):
	path = os.path.join(base_path, 'Layer_{}'.format(layer) + '_Tile_{}'.format(i+1) + '.png')
	image_list.append(cv2.imread(path))

im = ImageStitcher.ImageStitcher(rows, cols, overlap, image_list)
result = im.merge_stitching()

path = os.path.join(base_path, 'Layer_{}'.format(layer) + '_result.png')
cv2.imwrite(path, result)
#cv2.imshow("Image after stitching: ", result)
#cv2.waitKey(0)



end_time = time.time();
print("--- %s seconds ---" % (time.time() - start_time))
