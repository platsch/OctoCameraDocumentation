# -*- coding: utf-8 -*-
"""
    This file is part of OctoCameraDocumenation base on FragJackers OctoCameraDocumentation

    OctoCameraDocumentation is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OctoCameraDocumentation is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OctoCameraDocumentation.  If not, see <http://www.gnu.org/licenses/>.

    Main author: Florens Wasserfall <wasserfall@informatik.uni-hamburg.de>
    Dennis Struhs <dennis.struhs@hamburg.de>
"""

from __future__ import absolute_import


import octoprint.plugin
import flask
import re
from subprocess import call
import os
import time
import datetime
import base64
import shutil
import json
import struct
import imghdr
import cv2
import numpy as np

import time
import datetime

from collections import deque
from .GCode_processor import GCodeProcessor
from .GCode_processor import CustomJSONEncoder as CoordJSONify
from .GridGenerator import CameraGridMaker
from .ImageStitcher import ImageStitcher


__plugin_name__ = "OctoCameraDocumentation"
__plugin_version__ = "0.1"

#instantiate plugin object and register hook for gcode injection
def __plugin_load__():

    octocameradocumentation = OctoCameraDocumentation()

    global __plugin_implementation__
    __plugin_implementation__ = octocameradocumentation

    global __plugin_hooks__
    __plugin_hooks__ = {'octoprint.comm.protocol.gcode.queuing': octocameradocumentation.hook_gcode_queuing}


class OctoCameraDocumentation(octoprint.plugin.StartupPlugin,
            octoprint.plugin.TemplatePlugin,
            octoprint.plugin.EventHandlerPlugin,
            octoprint.plugin.SettingsPlugin,
            octoprint.plugin.AssetPlugin,
            octoprint.plugin.SimpleApiPlugin,
            octoprint.plugin.BlueprintPlugin):

    FEEDRATE = 4000.000


    def __init__(self):
        self.GCoordsList = []
        self.CameraGridCoordsList = []
        self.GridInfoList = []
        self.currentLayer = 0
        self.gridIndex = 0

        self.qeue = None

        self.CamPixelX = None
        self.CamPixelY = None

        self.our_pic_width = None
        self.our_pic_height = None

        self.currentPrintJobDir = None #Holds the current printjob folder dir

        self.mode = "normal" #Contains the mode for the camera callback

        self.image_array = [] #Stores the incoming images in an array
        self.MergedImage = None #Is created by stitching the tile images together

    def on_after_startup(self):
        #used for communication to UI
        self._pluginManager = octoprint.plugin.plugin_manager()

    # Add helpers from the auxilary OctoPNP plug-in to grab images and camera resolution
	helpers = self._pluginManager.get_helpers("OctoPNP", "get_head_camera_image", "get_head_camera_pxPerMM")
        if helpers and "get_head_camera_image" in helpers:
            self._logger.info("FOUND HELPER FOR TAKING IMAGE!!!")
            self.get_camera_image = helpers["get_head_camera_image"]
        if helpers and "get_head_camera_pxPerMM" in helpers:
            self._logger.info("FOUND HELPER FOR CAMERARESOLUTION!!!")
            self.get_camera_resolution = helpers["get_head_camera_pxPerMM"]

    def get_settings_defaults(self):
        return dict(target_folder = "C:\Desktop",
                    picture_width = 800,
                    picture_height = 800)

    def get_template_configs(self):
        return [
            dict(type="tab", template="OctoCameraDocumentation_tab.jinja2"),
            dict(type="settings", template="OctoCameraDocumentation_settings.jinja2")
        ]

    def get_assets(self):
        return dict(
            js=["js/OctoCameraDocumentation.js",
                "js/camGrid.js",
                "js/settings.js"]
        )

    # GET endpoint, provides image resolution for the settings UI
    def on_api_get(self, request):
        self.mode = "resolution_get"

        # Get an image to determine the camera resolution
        self.get_camera_image(0, 0, self.get_camera_image_callback, True)

        self.our_pic_width = None
        self.our_pic_height = None
        # As long as the variables are not here, send python to sleep
        while(self.our_pic_width is None or self.our_pic_height is None):
            time.sleep(1)
        return flask.jsonify(width = self.our_pic_width,
                             height = self.our_pic_height)

    # Use the on_event hook to extract XML data every time a new file has been loaded by the user
    def on_event(self, event, payload):
        #extraxt part informations from inline xmly
        if event == "FileSelected":
            #Retrieve the basefolder for the GCode uploads
            dir_name = self._settings.global_get_basefolder("uploads")
            base_filename = payload.get("path")
            uploadsPath = os.path.join(dir_name, base_filename)
            file = self._openGCodeFiles(uploadsPath)

            # Extract layer-wise gcodes
            gcode_processor = GCodeProcessor(file)
            self.GCoordsList = gcode_processor.gcodePerLayer()

            #Get the values for the Camera grid box sizes
            self._computeLookupGridValues()

            #Now create the actual grid
            self._createCameraGrid(
                self.GCoordsList,
                self.CamPixelX,
                self.CamPixelY)

            self._logger.info("Created the camera lookup grid succesfully from the file: %s", payload.get("file"))
            self._logger.info( "Current Target folder setting is: %s", self._settings.get(["target_folder"]))
            self._updateUI("FILE", "")

        # Create new Folder for dropping the images for the new printjob
        if(event == "PrintStarted"):
            self.currentPrintJobDir = self.getBasePath()
            os.mkdir(self.currentPrintJobDir)

    def _createCameraGrid(self,inputList,CamResX,CamResY):
        templist = []
        infoList = []
        count = 0
        while count < len(inputList):
            #Creates a new CameraGridMaker Object with int Numbers for the Cam resolution
            grid_maker = CameraGridMaker(inputList,count,CamResX,CamResY)

            infoList.append([grid_maker.getMaxX(),
                    grid_maker.getMinX(),
                    grid_maker.getMaxY(),
                    grid_maker.getMinY(),
                    grid_maker.getCenterX(),
                    grid_maker.getCenterY(),
                    grid_maker.getGridRows(),
                    grid_maker.getGridCols()])
            templist.append(grid_maker.getCameraCoords())
            count += 1

        #Retrieve the necessary variables to be forwarded to the Octoprint Canvas
        self.CameraGridCoordsList = templist
        self.GridInfoList = infoList


    """
    Use the gcode hook to start the camera grid documentation processes.
    """
    def hook_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if "M942" in cmd:
            if(self._printer.is_printing()):
                self._printer.pause_print()
            self._logger.info( "Qeued command to start the Camera documentation" )

            # Create the qeue for the printer camera coordinates
            self.qeue = deque(self.CameraGridCoordsList[self.currentLayer])
            elem = self.getNewQeueElem()
            self.get_camera_image(elem.x, elem.y, self.get_camera_image_callback, True)

            return "G4 P1" # return dummy command

    	if "M945" in cmd:
    	    self.currentPrintJobDir = self.getBasePath()
            os.mkdir(self.currentPrintJobDir)


    def get_camera_image_callback(self, path):
        print("Entered image processing callback")

        # Get the picture for the grid tiles here
        if(self.mode == "normal"):
            # Copy found files over to the target destination folder
            self.copyImageFiles(path)
            self._logger.info( "Copied Image to: %s", self.getBasePath() )
            # Get new element and continue tacking pictures if qeue not empty
            elem = self.getNewQeueElem()
            if(elem):
                self.get_camera_image(elem.x, elem.y, self.get_camera_image_callback, False)

        # Get the resolution for the settings button here
        if(self.mode == "resolution_get"):
            self.our_pic_width,self.our_pic_height = self._get_image_size(path)
            self._logger.info("The found image resolution was: %dx%d",self.our_pic_width,self.our_pic_width)
            self.mode = "normal" # Return to normal mode after finishing
        # else:
        #     return self._settings.get_int(["picture_width"]),
        #     self._settings.get_int(["picture_height"])

    def getNewQeueElem(self):
        if(self.qeue):
            self.gridIndex += 1 #Increment Tile after each deque
            return self.qeue.popleft()
        else:
            # Do image processing
            layer_config = self.GridInfoList[self.currentLayer]
            image_stitcher = ImageStitcher(layer_config[6], layer_config[7], self.image_array)
            layer_image = image_stitcher.merge_trivial()
            cv2.imwrite(os.path.join(self.currentPrintJobDir, "layer"+str(self.currentLayer)+".png"), layer_image)
            self.image_array = []


            self.currentLayer += 1 #Increment layer when qeue was empty
            self.gridIndex = 0 #Reset Grid Index
            if(self._printer.is_paused()):
                print "resume print"
                self._printer.resume_print()
            return(None)

    def copyImageFiles(self, srcpath):
        name, ext = os.path.splitext(os.path.basename(srcpath))
        dest = os.path.join(self.currentPrintJobDir, 'Layer_{}'.format(self.currentLayer) + '_Tile_{}'.format(self.gridIndex) + ext)
        shutil.copyfile(srcpath, dest)
        # and store into array for later processing
        self.image_array.append(cv2.imread(srcpath))

    def getBasePath(self):
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d__%H'+'h'+'_%M'+'m'+'_%S'+'s')
        return os.path.join(self._settings.get(["target_folder"]), 'Printjob_{}'.format(timestamp))

    def _openGCodeFiles(self, inputName):
        gcode = open( inputName, 'r' )
        readData = gcode.readlines()
        gcode.close()
        return readData

    def _moveCameraToCamGrid(self ,Xpos ,Ypos):
        # move camera to part position
        cmd = "G1 X" + str(Xpos) + " Y" + str(Ypos) + " F" + str(self.FEEDRATE)
        self._logger.info("Move camera to: %s , %s",Xpos,Ypos)
        self._printer.commands(cmd)


    def _computeLookupGridValues(self):
        PixelPerMillimeter = self.get_camera_resolution("HEAD")
        # Divide the resolution by the PixelPerMillimeter ratio
        self.CamPixelX = self._settings.get_int(["picture_width"]) / PixelPerMillimeter['x']
        self.CamPixelY = self._settings.get_int(["picture_height"]) / PixelPerMillimeter['y']

    """This function retrieves the resolution of the .png, .gif or .jpeg image file passed into it.
    This function was copypasted from https://stackoverflow.com/questions/8032642/how-to-obtain-image-size-using-standard-python-class-without-using-external-lib
    :param fname: Contains the filename of the file """
    def _get_image_size(self, fname):
        with open(fname, 'rb') as fhandle:
            head = fhandle.read(24)
            if len(head) != 24:
                return
            if imghdr.what(fname) == 'png':
                check = struct.unpack('>i', head[4:8])[0]
                if check != 0x0d0a1a0a:
                    return
                width, height = struct.unpack('>ii', head[16:24])
            elif imghdr.what(fname) == 'gif':
                width, height = struct.unpack('<HH', head[6:10])
            elif imghdr.what(fname) == 'jpeg':
                try:
                    fhandle.seek(0) # Read 0xff next
                    size = 2
                    ftype = 0
                    while not 0xc0 <= ftype <= 0xcf:
                        fhandle.seek(size, 1)
                        byte = fhandle.read(1)
                        while ord(byte) == 0xff:
                            byte = fhandle.read(1)
                        ftype = ord(byte)
                        size = struct.unpack('>H', fhandle.read(2))[0] - 2
                    # We are at a SOFn block
                    fhandle.seek(1, 1)  # Skip `precision' byte.
                    height, width = struct.unpack('>HH', fhandle.read(4))
                except Exception: #IGNORE:W0703
                    return
            else:
                return
            return width, height

    def _updateUI(self, event, parameter):
        data = dict(
            info="dummy"
        )
        if (event == "FILE"):
            if (self.GCoordsList != None):
                # compile part information
                data = dict(
                    gcodeCoordinates = json.dumps(self.GCoordsList,cls=CoordJSONify),
                    cameraCoordinates = json.dumps(self.CameraGridCoordsList,cls=CoordJSONify),
                    gridInfoList = json.dumps(self.GridInfoList,cls=CoordJSONify),
                    CamPixelResX = self.CamPixelX,
                    CamPixelResY = self.CamPixelY,
                )
        elif event is "HEADIMAGE":
            # open image and convert to base64
            f = open(parameter,"r")
            data = dict(
                src = "data:image/" + os.path.splitext(parameter)[1] + ";base64,"+base64.b64encode(bytes(f.read()))
            )

        message = dict(
            event=event,
            data=data
        )
        self._pluginManager.send_plugin_message(__plugin_name__, message)
