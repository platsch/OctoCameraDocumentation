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

gcode_file = "testimages/conductive/cube_wires.gcode"
image_file = "testimages/conductive/Layer_3_result.png"
result_file = "testimages/conductive/result.png"
overlay_file = "testimages/conductive/overlay.png"
csv_bgr_file = "testimages/conductive/pixels_bgr.csv"
csv_hsv_file = "testimages/conductive/pixels_hsv.csv"
label_file = "testimages/conductive/label.png"
layer = 3

# import gcode file
gcode = open(gcode_file, 'r')
readData = gcode.readlines()
gcode.close()
gcode_processor = GCodeProcessor.GCodeProcessor(readData, 1)
gcode_list = gcode_processor.gcodePerLayer()

grid_maker = GridGenerator.CameraGridMaker(gcode_list,layer,14.76015,14.76015)
grid = grid_maker.getCameraCoords()

# open image
image = cv2.imread(image_file)

start_time = time.time()

ia = ImageAnalyzer.ImageAnalyzer(gcode_list[layer], image, 54.2, 54.3, grid_maker.getMinX(), grid_maker.getMinY(), grid_maker.getMaxX(), grid_maker.getMaxY())
mask = ia.extruder_mask(1, 0.5)

result = cv2.bitwise_and(image, image, mask=mask)
cv2.imwrite(result_file, result)

inverse_mask = 255 - mask
overlay = cv2.bitwise_or(image, image, mask=inverse_mask)
cv2.imwrite(overlay_file, overlay)


# Export pixel csv
pixels_0 = ia.extruder_pixels(0, 0.3, HSV=True, limit = 0)
pixels_1 = ia.extruder_pixels(1, 0.5, HSV=True, limit = 0)

# take random subsample
svc_samples = 1000
if(pixels_0.shape[0] > svc_samples):
	idx = np.random.randint(pixels_0.shape[0], size=svc_samples)
	pixels_0 = pixels_0[idx,:]
if(pixels_1.shape[0] > svc_samples):
	idx = np.random.randint(pixels_1.shape[0], size=svc_samples)
	pixels_1 = pixels_1[idx,:]

# plot color distribution
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlabel("H / Blue")
ax.set_ylabel("S / Green")
ax.set_zlabel("V / Red")
#ax.scatter(pixels_0[:, 0], pixels_0[:, 1], pixels_0[:, 2], c="red", s = 0.5)
#ax.scatter(pixels_1[:, 0], pixels_1[:, 1], pixels_1[:, 2], c="black", s = 0.5)
#plt.show()


# prepare CSV data
pixels = np.vstack((pixels_0, pixels_1))
class_0 = np.zeros(pixels_0.shape[0], dtype=int)
class_1 = np.ones(pixels_1.shape[0], dtype=int)
classes = np.hstack((class_0, class_1))

#train svm
clf = LinearSVC(max_iter = 1000, dual = False, tol = 1e-5, verbose = 1)
clf.fit(pixels, classes)


# mark missing ink
#label_img = image
label_img = result

for row in range(label_img.shape[0]):
	row_labels = clf.predict(label_img[row,:,:])
	label_img[row,:,:][np.equal(row_labels, 0)] = [0, 0, 255]


cv2.imwrite(label_file, label_img)


end_time = time.time();
print("--- %s seconds ---" % (time.time() - start_time))
