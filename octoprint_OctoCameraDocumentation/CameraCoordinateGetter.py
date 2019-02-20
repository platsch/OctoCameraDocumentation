'''
Created on 18.07.2017
@author: Florens Wasserfall, Dennis Struhs
'''

from GCode_processor import Coordinate
from copy import deepcopy

class CameraGridMaker:
    #Stores the maximum Pixel size the camera provies. Its in Pixel x Pixel Format
    CamResX = None
    CamResY = None

    #Below values store the extreme values found during the processing process
    minX = None
    minY = None
    maxX = None
    maxY = None

    def __init__(self,layerGCode,layer,CamResX,CamResY):
        self.CamResX = CamResX
        self.CamResY = CamResY
        self.rows = 0
        GCode = layerGCode[layer]

        # find bounding box
        if(len(GCode) > 0):
            self.minX = GCode[0].x
            self.maxX = GCode[0].x
            self.minY = GCode[0].y
            self.maxY = GCode[0].y

        for c in GCode:
            if(c.x < self.minX):
                self.minX = c.x
            if(c.x > self.maxX):
                self.maxX = c.x
            if(c.y < self.minY):
                self.minY = c.y
            if(c.y > self.maxY):
                self.maxY = c.y


    # return list of coordinates where images should be taken
    def getCameraCoords(self):
        result = []
        # do we have any data?
        if self.minX is not None:
            x_range = abs(self.maxX - self.minX)
            y_range = abs(self.maxY - self.minY)
            rows = int(x_range / self.CamResX) +1
            cols = int(y_range / self.CamResY) +1

            x_start_offset = (rows * self.CamResX - x_range) / 2
            y_start_offset = (cols * self.CamResY - y_range) / 2
            x = self.minX - x_start_offset
            y = self.minY - y_start_offset
            for col in range(cols):
                for row in range(rows):
                    result.append(Coordinate(x + self.CamResX/2, y + self.CamResY/2))
                    x += self.CamResX
                y += self.CamResY
                x = self.minX - x_start_offset

        #result.append(Coord)
        return result


    def getMinX(self):
        return self.minX

    def getMaxX(self):
        return self.maxX

    def getMinY(self):
        return self.minY

    def getMaxY(self):
        return self.maxY

    def getCenterX(self):
        return ((self.maxX - self.minX) / 2) + self.minX

    def getCenterY(self):
        return ((self.maxY - self.minY) / 2) + self.minY