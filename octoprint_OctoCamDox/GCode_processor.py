'''
Created on 03.06.2017

@author: Dennis Struhs

'''

import re
import json

#===============================================================================
# RegEx Pattern to retrieve the info from the file
# extractFileInfo = re.match('.*X:\s*(\d+.\d+).*Y:\s*(\d+.\d+', line)
#===============================================================================

#===============================================================================
# Help Classes
#===============================================================================

class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y

#Offers serialization of the Coordinate custom Object
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Coordinate):
            return [o.x, o.y]
        return CustomJSONEncoder(self, o)

#===============================================================================
# Main class
#===============================================================================
class CameraGCodeExtraction:

    desiredExtruder = ''
    z_stepping = 0.0
    currentLayer = 1
    Z_layer = 0.0

    #Z_layer = 1.0           #Define the Z-Layer Threshold where the T1 extruder is working at
    current_extruder = ''   #Stores the currently selected Extruder beein T0/T1
    currentExtruderZPos = 0.0      #Stores the last Z Position of the extruder
    lastExtruderZPos = 0.0

    shortCoordList = None
    masterCoordList = None

    #desiredExtruder = raw_input('Enter your input Extruder: ')
    #Z_layer = float(raw_input('Enter your input Layer: '))

    """The instantiation function for the incoming values
    :param zSteps: Holds the value how thick a layer is. For example 0.25
    :param targetExtruder: Specifies the monitored Extruder. For example T0"""
    def __init__(self,zSteps,targetExtruder):
        self.desiredExtruder = targetExtruder
        self.z_stepping = float(zSteps)
        self.Z_layer = self.z_stepping * self.currentLayer
        # Initialize lists
        self.shortCoordList = []
        self.masterCoordList = []

    """The main function to handle the extraction of the GCode information from
    a given testfile
    :param Data: Contains the textdata for processing"""
    def extractCameraGCode(self, Data):
        zWorkList = self.findAllZValues(Data)
        for eachItem in zWorkList:
            self.Z_layer = eachItem
            self.findAllGCodesInLayer(Data)
        self.swapfirstArrayEntries()

    """Finds all layers for further processing
    :param Data: Contains the textdata for processing"""
    def findAllZValues(self,Data):
        zValueList = []
        previousZ = 0.0
        currentZ = 0.0
        for line in Data:
            z_values = re.match('G1 Z(\d+.\d+)', line)

            if(self.validZValues(z_values)):
                # Check if new Z value is smaller to filter unwanted values
                previousZ = currentZ
                currentZ = z_values.group(1)
                if(not zValueList.__contains__(float(z_values.group(1)))
                    and currentZ < previousZ):
                    zValueList.append(float(z_values.group(1)))
        return zValueList

    """Do some RegEx to find the entries of value for us.
    :param Data: Contains the textdata for processing
    """
    def findAllGCodesInLayer(self, Data):
        for line in Data:
            self.extruder_state = re.match('T\d', line)
            z_values = re.match('G1 Z(\d+.\d+)', line)
            #Get the currently selected extruder from File (T1 or T0)
            if self.extruder_state != None:
                self.current_extruder = self.extruder_state.group(0)
            #Get the last Z Position value of the T0 exrruder
            if self.properSelectedExtruder(z_values):
                self.currentExtruderZPos = float(z_values.group(1))

            #Get the X and Y values of the extruder at the specified layer
            if self.extruder_working(self.desiredExtruder):
                xy_values = re.match('G1 X(\d+.\d+) Y(\d+.\d+)', line)
                if xy_values != None:
                    newCoord = Coordinate(
                        float(xy_values.group(1)),
                        float(xy_values.group(2)))
                    self.shortCoordList.append(newCoord)

        # Make sure the list has enough entries
        if(len(self.shortCoordList) >= 2):
            self.masterCoordList.append(self.shortCoordList)

        self.shortCoordList = []

#===============================================================================
# Help functions
#===============================================================================

    def swapfirstArrayEntries(self):
        mylist = self.masterCoordList
        mylist[0],mylist[1] = mylist[1],mylist[0]

    def getCoordList(self):
        return self.masterCoordList

    def properSelectedExtruder(self, z_values):
        return self.validZValues(z_values) and self.current_extruder == self.desiredExtruder

    def validZValues(self, z_values ):
        return z_values != None

    def extruder_working(self, inputExtruder):
        return self.currentExtruderZPos == self.Z_layer and self.current_extruder == inputExtruder

#===============================================================================
# writeFiles(CoordList, desiredExtruder + "_ExtruderPositions.txt")
# writeFiles(shortCoordList, desiredExtruder + "_positions.txt")
#===============================================================================

#===============================================================================
# Old legacy Code
#===============================================================================
#===============================================================================
# #Do some RegEx to find the entries of value for us.
# for line in Data:
#     extruder_state = re.match( 'T\d', line )
#     z_values = re.match( 'G1 Z(\d+.\d+)', line )
#
#     #Get the currently selected extruder from File (T1 or T0)
#     if extruder_state != None:
#         current_extruder = extruder_state.group( 0 )
#
#     #Get the last Z Position value of the T1 exrruder
#     if validZValues( z_values ) and current_extruder == desiredExtruder:
#         currentExtruderZPos = float( z_values.group( 1 ) )
#
#     #Get the X and Y values of the extruder at the specified layer
#     if extruder_working(desiredExtruder):
#         xy_values = re.match( 'G1 X(\d+.\d+) Y(\d+.\d+)', line )
#         if xy_values != None:
#             CoordList.append(desiredExtruder
#             + ' Extruder is at X: {}'.format( xy_values.group(1) )
#             + ', Y: {}'.format( xy_values.group(2) )
#             + ', in Z-Layer: {}'.format( currentExtruderZPos ) + '\n')
#             newCoord = Coordinate(xy_values.group(1),xy_values.group(2))
#             shortCoordList.append(newCoord)
#===============================================================================
