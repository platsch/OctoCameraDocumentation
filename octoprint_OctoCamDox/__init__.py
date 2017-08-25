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
        self.currentLayer = 0

        self.maxX = 0.0
        self.maxY = 0.0
        self.minX = 0.0
        self.minY = 0.0
        self.centerY = 0.0
        self.centerX = 0.0
        self.CamPixelX = 0
        self.CamPixelY = 0


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
            self.currentLayer = 1
            self.CamPixelX = 50
            self.CamPixelY = 50

            self._createCameraGrid(
                self.GCoordsList,
                self.currentLayer,
                self.CamPixelX,
                self.CamPixelY)

            self._logger.info("Created the camera lookup grid succesfully from the file: %s", payload.get("file"))
            self._updateUI("FILE", "")


    def _createCameraGrid(self,inputList,onLayer,CamResX,CamResY):
        Image = ImageOperations()
        Image.createBackgroundImage()

        #Creates a new CameraGridMaker Object with int Numbers for the Cam resolution
        newGridMaker = CameraGridMaker(inputList,onLayer,CamResX,CamResY)

        #Execute all necessary operations to create the actual CameraGrid
        newGridMaker.getCoordinates()
        newGridMaker.drawGCodeLines(Image)
        newGridMaker.createCameraLookUpGrid()
        newGridMaker.drawAllFoundCameraPositions(Image)
        newGridMaker.drawCameraLines(Image)

        #Retrieve the necessary variables to be forwarded to the Octoprint Canvas
        self.CameraGridCoordsList = newGridMaker.getCameraCoords()
        self.maxX = newGridMaker.getMaxX()
        self.maxY = newGridMaker.getMaxY()
        self.minX = newGridMaker.getMinX()
        self.minY = newGridMaker.getMinX()
        self.centerY = newGridMaker.getCenterY()
        self.centerX = newGridMaker.getCenterX()
        self.CamPixelX = newGridMaker.getCampixelX()
        self.CamPixelY = newGridMaker.getCampixelY()

        #Image.drawGridBox(0, 0, 50, 50)
        #Draw Maximums and Minimums
        Image.drawExtremaBounds()
        #Draw Center of of the Extremes
        #Image.drawCenterCircle(int(centerX), int(centerY))
        #Image.drawBoxFromCenter(int(centerX), int(centerY))
        # Resize the Image
        Image.resizeImage(1024, 1024)
        #Image.saveImage('Camera Grid')
        WindowText = "Suggested Camera Grid on Layer " + str(onLayer)
        Image.showImage(WindowText)


    """
    Use the gcode hook to interrupt the printing job on custom M361 commands.
    """
    def hook_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if "M361" in cmd:
            if self._state == self.STATE_NONE:
                self._state = self.STATE_PICK
                if self._printer.get_current_data()["currentZ"]:
                    self._currentZ = float(self._printer.get_current_data()["currentZ"])
                else:
                    self._currentZ = 0.0
                command = re.search("P\d*", cmd).group() #strip the M361
                self._currentPart = int(command[1:])

                self._logger.info( "Received M361 command to place part: " + str(self._currentPart))

                self._updateUI("OPERATION", "pick")


                self._logger.info( "Move camera to part: " + str(self._currentPart))
                self._moveCameraToPart(self._currentPart)

                self._printer.commands("M400")
                self._printer.commands("G4 P1")
                self._printer.commands("M400")

                for i in range(5):
                    self._printer.commands("G4 P1")

                self._printer.commands("M362")

                for i in range(5):
                    self._printer.commands("G4 P1")

                return "G4 P1" # return dummy command
            else:
                self._logger.info( "ERROR, received M361 command while placing part: " + str(self._currentPart))

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
        if "M362" in cmd:
            if self._state == self.STATE_PICK:
                self._state = self.STATE_ALIGN
                self._logger.info("Pick part " + str(self._currentPart))

                for i in range(3):
                    self._printer.commands("G4 P50")

                self._pickPart(self._currentPart)
                self._printer.commands("M400")
                self._printer.commands("G4 P1")
                self._printer.commands("M400")

                for i in range(5):
                    self._printer.commands("G4 P1")

                self._printer.commands("M362")

                for i in range(5):
                    self._printer.commands("G4 P1")

                return "G4 P1" # return dummy command

            if self._state == self.STATE_ALIGN:
                self._state = self.STATE_PLACE
                self._logger.info("Align part " + str(self._currentPart))

                for i in range(3):
                    self._printer.commands("G4 P10")

                self._alignPart(self._currentPart)
                self._printer.commands("M400")
                self._printer.commands("G4 P1")
                self._printer.commands("M400")

                for i in range(10):
                    self._printer.commands("G4 P1")

                self._printer.commands("M362")

                for i in range(5):
                    self._printer.commands("G4 P1")

                return "G4 P1" # return dummy command

            if self._state == self.STATE_PLACE:
                self._logger.info("Place part " + str(self._currentPart))

                for i in range(3):
                    self._printer.commands("G4 P10")

                self._placePart(self._currentPart)
                self._printer.commands("M400")
                self._printer.commands("G4 P1")
                self._printer.commands("M400")

                for i in range(10):
                    self._printer.commands("G4 P1")

                self._logger.info("Finished placing part " + str(self._currentPart))
                self._state = self.STATE_NONE
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
                    gcodeCoordinates = json.dumps(self.GCoordsList[1],cls=CoordJSONify),
                    cameraCoordinates = json.dumps(self.CameraGridCoordsList,cls=CoordJSONify),
                    maximumX = self.maxX,
                    maximumY = self.maxY,
                    minimumX = self.minX,
                    minimumY = self.minY,
                    centerPosY = self.centerY,
                    centerPosX = self.centerX,
                    CamPixelResX = self.CamPixelX,
                    CamPixelResY = self.CamPixelY,
                    currentselectedLayer = self.currentLayer
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
