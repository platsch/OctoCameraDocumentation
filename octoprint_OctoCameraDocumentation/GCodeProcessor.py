'''
Created on 03.06.2017
@author: Dennis Struhs

'''

import re
import json

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
class GCodeProcessor:

    gcode = None

    def __init__(self, gcode):
        self.gcode = gcode

    def gcodePerLayer(self):
        result = []
        if self.gcode is not None:
            layer = []
            for line in self.gcode:
                # append normal extrusion lines
                extrusion = re.match('G1 X(\d+.\d+) Y(\d+.\d+) E\d+.\d+', line)
                if extrusion is not None:
                    layer.append(Coordinate(float(extrusion.group(1)), float(extrusion.group(2))))

                # look for layer changes
                layer_change = re.match('M942', line)
                if layer_change is not None:
                    result.append(layer)
                    layer = []

        return result
