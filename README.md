# OctoCameraDocumentation
OctoCameraDocumentation is a Plugin for Octoprint which allows to automatically document and analyze the print process layer by layer with very high resolution.
It requires a camera mounted at the printhead next to the extruder to take a set of images from short distance after each layer was printed. The tiles are then stitched together into one image per layer.


![OctoCamDox-Overview](https://user-images.githubusercontent.com/19975052/31948581-95886530-b8d7-11e7-80ec-65bee74951a3.JPG)

# Installation
## Prerequirements
OctoCameraDocumentation requires [OctoPNP](https://github.com/platsch/OctoPNP) to be installed and the head camera correctly configured to record images. OctoPNP takes care of queue handling and camera positioning and provides a helper function to give other plugins access to the cameras.

## Installing the package
The plugin itself can be installed as any regular python package:
`pip install https://github.com/platsch/OctoCameraDocumentation/archive/master.zip`

Make sure you use the same Python environment that you installed OctoPrint under, otherwise the plugin won't be able to satisfy its dependencies. Further information can be found in the Octoprint [documentation](http://docs.octoprint.org/en/devel/plugins/using.html)
OctoCameraDocumentation requires numpy and opencv2. Try installing those packages by hand if automatic dependency resolving fails. The experimental image Analyzer additionaly requires sklearn and matplotlib.

# GCode configuration
The documentation is triggered by custom M942 commands in the gcode, which should be inserted at the end of each layer right befor the Z-position is updated to the next layer (layer change gcode). No further adaption is required for the gcode. The spatial extent of each layer is automatically detected upon loading the gcode-file. OctoCameraDocumentation generates an individual tile grid for each layer to optimize coverage.

# Plugin Configuration
Good configuration and calibration of the printer is absolutely crucial to successfully generate accurate images. Special attention should be paid to thorough backlash calibration, measuring the offset of the camera to the primary extruder and setting an accurate `Pixel/MM` value for the head camera in OctoPNP.

The plugin setting should mostly be self-explaining. The Image size can be automatically obtained by pressing the "Get picture resolution" button. The `Overlap` setting detemines how much the individual tiles should be overlapping for correlation based image stitching.
