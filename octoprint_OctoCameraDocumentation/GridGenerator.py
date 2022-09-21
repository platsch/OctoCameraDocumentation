# -*- coding: utf-8 -*-
'''
Created on 18.07.2017
@author: Florens Wasserfall, Dennis Struhs
'''

from __future__ import absolute_import, division, print_function, unicode_literals

from .GCodeProcessor import Coordinate
from copy import deepcopy

class CameraGridMaker:
    #Stores the maximum Pixel size the camera provies. Its in Pixel x Pixel Format
    CamResX = None
    CamResY = None

    #Below values store the extreme values found during the processing process
    minX = float('inf')
    minY = float('inf')
    maxX = float('-inf')
    maxY = float('-inf')

    def __init__(self,layerGCode,layer,CamResX,CamResY):
        self.CamResX = CamResX
        self.CamResY = CamResY
        self.rows = 0
        GCode = layerGCode[layer]

        # find bounding box
        for tool in GCode:
            for c in tool:
                for p in [c.a, c.b]:
                    if(p.x < self.minX):
                        self.minX = p.x
                    if(p.x > self.maxX):
                        self.maxX = p.x
                    if(p.y < self.minY):
                        self.minY = p.y
                    if(p.y > self.maxY):
                        self.maxY = p.y


    # return list of coordinates where images should be taken
    def getCameraCoords(self):
        result = []
        # do we have any data?
        if self.minX < float('inf') and self.minY < float('inf') and self.maxX > float('-inf') and self.maxY > float('-inf'):
            x_range = abs(self.maxX - self.minX)
            y_range = abs(self.maxY - self.minY)
            rows = self.getGridRows()
            cols = self.getGridCols()

            x_start_offset = (cols * self.CamResX - x_range) / 2
            y_start_offset = (rows * self.CamResY - y_range) / 2
            x = self.minX - x_start_offset
            y = self.minY - y_start_offset
            for row in range(rows):
                for col in range(cols):
                    result.append(Coordinate(x + self.CamResX/2, y + self.CamResY/2))
                    x += self.CamResX
                y += self.CamResY
                x = self.minX - x_start_offset

        return result

    def getGridRows(self):
        if self.minY < float('inf') and self.maxY > float('-inf'):
            y_range = abs(self.maxY - self.minY)
            return int(y_range / self.CamResY) +1
        else:
            return 0

    def getGridCols(self):
        if self.minX < float('inf') and self.maxX > float('-inf'):
            x_range = abs(self.maxX - self.minX)
            return int(x_range / self.CamResX) +1
        else:
            return 0

    def getMinX(self):
        return self.minX

    def getMaxX(self):
        return self.maxX

    def getMinY(self):
        return self.minY

    def getMaxY(self):
        return self.maxY

    def getCenterX(self):
        return (self.minX + self.maxX) / 2

    def getCenterY(self):
        return (self.minY + self.maxY) / 2