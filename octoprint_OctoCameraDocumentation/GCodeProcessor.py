'''
Created on 03.06.2017
@author: Florens Wasserfall, Dennis Struhs

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
class Line:
    def __init__(self, a, b):
        self.a = a
        self.b = b

#Offers serialization of the Coordinate custom Object
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Coordinate):
            return [o.x, o.y]
        if isinstance(o, Line):
            return [[o.a.x, o.a.y], [o.b.x, o.b.y]]
        return CustomJSONEncoder(self, o)

#===============================================================================
# Main class
#===============================================================================
class GCodeProcessor:
    gcode = None
    max_extruder_num = 0

    def __init__(self, gcode, max_extruder_num):
        self.gcode = gcode
        self.max_extruder_num = max_extruder_num

    def gcodePerLayer(self):
        result = []
        if self.gcode is not None:
            layer = []
            tool = 0
            # initialize all extruders
            for i in range(self.max_extruder_num+1):
                layer.append([])

            last_position = None

            for line in self.gcode:
                # append normal extrusion lines
                extrusion = re.match('G1 X(\d+.\d+) Y(\d+.\d+) E\d+.\d+', line)
                if extrusion is not None:
                    layer[tool].append(Line(last_position, Coordinate(float(extrusion.group(1)), float(extrusion.group(2)))))

                # store last position
                position = re.match('G1 X(\d+.\d+) Y(\d+.\d+)', line)
                if position is not None:
                    last_position = Coordinate(float(position.group(1)), float(position.group(2)))

                # tool changes
                extruder = re.match('T\d', line)
                if extruder is not None:
                    tool = int(extruder.group(0)[1])

                # look for layer changes
                layer_change = re.match('M942', line)
                if layer_change is not None:
                    result.append(layer)
                    layer = []
                    # initialize all extruders
                    for i in range(self.max_extruder_num+1):
                        layer.append([])

        return result
