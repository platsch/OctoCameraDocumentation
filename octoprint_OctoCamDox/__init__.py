# -*- coding: utf-8 -*-
"""
    This file is part of OctoCamDox

    OctoCamDox is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OctoCamDox is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OctoCamDox.  If not, see <http://www.gnu.org/licenses/>.

    Main author: Dennis Struhs <dennis.struhs@hamburg.de>
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

from .GCode_processor import CameraGCodeExtraction as GCodex
from .GCode_processor import CustomJSONEncoder as CoordJSONify
from .CameraCoordinateGetter import CameraGridMaker,ImageOperations


__plugin_name__ = "OctoCamDox"

#instantiate plugin object and register hook for gcode injection
def __plugin_load__():

    octocamdox = OctoCamDox()

    global __plugin_implementation__
    __plugin_implementation__ = octocamdox

    global __plugin_hooks__
    __plugin_hooks__ = {'octoprint.comm.protocol.gcode.sending': octocamdox.hook_gcode_sending, 'octoprint.comm.protocol.gcode.queuing': octocamdox.hook_gcode_queuing}


class OctoCamDox(octoprint.plugin.StartupPlugin,
            octoprint.plugin.TemplatePlugin,
            octoprint.plugin.EventHandlerPlugin,
            octoprint.plugin.SettingsPlugin,
            octoprint.plugin.AssetPlugin,
            octoprint.plugin.SimpleApiPlugin,
            octoprint.plugin.BlueprintPlugin):

    STATE_NONE = 0
    STATE_PICK = 1
    STATE_ALIGN = 2
    STATE_PLACE = 3

    FEEDRATE = 4000.000


    def __init__(self):
        self._state = self.STATE_NONE
        self._currentPart = 0
        self._currentZ = None
        self.GCoordsList = []
        self.CameraGridCoordsList = []
        self.GridInfoList = []
        self.currentLayer = 0

        self.CamPixelX = 15
        self.CamPixelY = 15


    def on_after_startup(self):
    #     self.imgproc = ImageProcessing(
    #         float(self._settings.get(["tray", "boxsize"])),
    #         int(self._settings.get(["camera", "bed", "binary_thresh"])),
    #         int(self._settings.get(["camera", "head", "binary_thresh"])))
    #     #used for communication to UI
        self._pluginManager = octoprint.plugin.plugin_manager()


    def get_settings_defaults(self):
        return {
            #"publicHost": None,
            #"publicPort": None,
            "tray": {
                "x": 0,
                "y": 0,
                "z": 0,
                "rows" : 5,
                "columns": 5,
                "boxsize": 10,
                "rimsize": 1.0
            },
            "vacnozzle": {
                "x": 0,
                "y": 0,
                "z_pressure": 0,
                "extruder_nr": 2,
                "grip_vacuum_gcode": "M340 P0 S1200",
                "release_vacuum_gcode": "M340 P0 S1500",
                "lower_nozzle_gcode": "",
                "lift_nozzle_gcode": ""
            },
            "camera": {
                "head": {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "path": "",
                    "binary_thresh": 150,
                    "grabScriptPath": ""
                },
                "bed": {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "pxPerMM": 50.0,
                    "path": "",
                    "binary_thresh": 150,
                    "grabScriptPath": ""
                },
                "image_logging": False
            }
        }

    def get_template_configs(self):
        return [
            dict(type="tab", template="OctoCamDox_tab.jinja2"),
            dict(type="settings", template="OctoCamDox_settings.jinja2")
            #dict(type="settings", custom_bindings=True)
        ]

    def get_assets(self):
        return dict(
            js=["js/OctoCamDox.js",
                "js/camGrid.js",
                "js/settings.js"]
        )

    # Flask endpoint for the GUI to request camera images. Possible request parameters are "BED" and "HEAD".
    @octoprint.plugin.BlueprintPlugin.route("/camera_image", methods=["GET"])
    def getCameraImage(self):
        result = ""
        if "imagetype" in flask.request.values:
            camera = flask.request.values["imagetype"]
            if ((camera == "HEAD") or (camera == "BED")):
                if self._grabImages(camera):
                    imagePath = self._settings.get(["camera", camera.lower(), "path"])
                    try:
                        f = open(imagePath,"r")
                        result = flask.jsonify(src="data:image/" + os.path.splitext(imagePath)[1] + ";base64,"+base64.b64encode(bytes(f.read())))
                    except IOError:
                        result = flask.jsonify(error="Unable to open Image after fetching. Image path: " + imagePath)
                else:
                    result = flask.jsonify(error="Unable to fetch image. Check octoprint log for details.")
        return flask.make_response(result, 200)

    # Use the on_event hook to extract XML data every time a new file has been loaded by the user
    def on_event(self, event, payload):
        #extraxt part informations from inline xmly
        if event == "FileSelected":
            #Initilize the Cameraextractor Class
            newCamExtractor = GCodex(0.25,'T0')
            #Retrieve the basefolder for the GCode uploads
            uploadsPath = self._settings.global_get_basefolder("uploads") + "\\" + payload.get("path")

            self._currentPart = None
            xml = "";
            f = self._openGCodeFiles(uploadsPath)
            #f = open(testPath, 'r')

            #Extract the GCodes for the CameraPath Algortihm
            newCamExtractor.extractCameraGCode(f)

            self.GCoordsList = newCamExtractor.getCoordList()

            self._createCameraGrid(
                self.GCoordsList,
                self.CamPixelX,
                self.CamPixelY)

            self._logger.info("Created the camera lookup grid succesfully from the file: %s", payload.get("file"))
            self._updateUI("FILE", "")


    def _createCameraGrid(self,inputList,CamResX,CamResY):
        Image = ImageOperations()
        Image.createBackgroundImage()

        templist = []
        infoList = []
        count = 0
        while count < len(inputList):
            #Creates a new CameraGridMaker Object with int Numbers for the Cam resolution
            newGridMaker = CameraGridMaker(inputList,count,CamResX,CamResY)

            #Execute all necessary operations to create the actual CameraGrid
            newGridMaker.getCoordinates()
            newGridMaker.createCameraLookUpGrid()

            infoList.append([newGridMaker.getMaxX(),
                    newGridMaker.getMinX(),
                    newGridMaker.getMaxY(),
                    newGridMaker.getMinY(),
                    newGridMaker.getCenterX(),
                    newGridMaker.getCenterY()])
            templist.append(newGridMaker.getCameraCoords())
            count += 1

        #Retrieve the necessary variables to be forwarded to the Octoprint Canvas
        self.CameraGridCoordsList = templist
        self.GridInfoList = infoList


    """
    Use the gcode hook to interrupt the printing job on custom C420 commands.
    """
    def hook_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if "M942" in cmd:
            self._logger.info( "Qeued command to start the Camera documentation" )

            for eachItem in self.CameraGridCoordsList[0]:
                self._logger.info( "Move camera to position X: %d Y: %d", eachItem.x, eachItem.y)

            return "G4 P1" # return dummy command

    """
    This hook is designed as some kind of a "state machine". The reason is,
    that we have to circumvent the buffered gcode execution in the printer.
    To take a picture, the buffer must be emptied to ensure that the printer has executed all previous moves
    and is now at the desired position. To achieve this, a M400 command is injected after the
    camera positioning command, followed by a M362. This causes the printer to send the
    next acknowledging ok not until the positioning is finished. Since the next command is a M362,
    octoprint will call the gcode hook again and we are back in the game, iterating to the next state.
    Since both, Octoprint and the printer firmware are using a queue, we inject some "G4 P1" commands
    as a "clearance buffer". Those commands simply cause the printer to wait for a millisecond.
    """

    def hook_gcode_sending(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if "M943" in cmd:
            self._logger.info("Start camera documentation process")

            for i in range(3):
                self._printer.commands("G4 P50")

            self._printer.commands("M400")
            self._printer.commands("G4 P1")
            self._printer.commands("M400")

            for i in range(5):
                self._printer.commands("G4 P1")

            self._printer.commands("M362")

            for i in range(5):
                self._printer.commands("G4 P1")

            return "G4 P1" # return dummy command

    def _openGCodeFiles(self, inputName):
        gcode = open( inputName, 'r' )
        readData = gcode.readlines()
        gcode.close()
        return readData

    def _grabImages(self, camera):
        result = True
        grabScript = "";
        if(camera == "HEAD"):
            grabScript = self._settings.get(["camera", "head", "grabScriptPath"])
        if(camera == "BED"):
            grabScript = self._settings.get(["camera", "bed", "grabScriptPath"])
        #os.path.dirname(os.path.realpath(__file__)) + "/cameras/grab.sh"
        try:
            if call([grabScript]) != 0:
                self._logger.info("ERROR: " + camera + " camera not ready!")
                result = False
        except:
            self._logger.info("ERROR: Unable to execute " + camera + " camera grab script!")
            self._logger.info("Script path: " + grabScript)
            result = False
        return result

    def _saveDebugImage(self, path):
        name, ext = os.path.splitext(os.path.basename(path))
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H:%M:%S')
        filename = "/" + name + "_" + timestamp + ext
        dest_path = os.path.dirname(path) + filename
        shutil.copy(path, dest_path)
        self._logger.info("saved %s image to %s", name, dest_path)


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
        elif event == "OPERATION":
            data = dict(
                type = parameter,
                part = self._currentPart
            )
        elif event == "ERROR":
            data = dict(
                type = parameter,
            )
            if self._currentPart: data["part"] = self._currentPart
        elif event == "INFO":
            data = dict(
                type = parameter,
            )
        elif event is "HEADIMAGE" or event is "BEDIMAGE":
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
