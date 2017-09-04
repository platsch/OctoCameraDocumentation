$(function() {
    function OctoCamDoxViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];
        self.control = parameters[1];
        self.connection = parameters[2];

        var _cameraGrid = {};
        var _cameraGridCanvas = document.getElementById('camGridCanvas');

        self.stateString = ko.observable("No file loaded");
        self.cameraResolution = ko.observable("");
        self.debugvar = ko.observable("");
        self.CamGridHeader = ko.observable("Camera lookup grid");

        self.layerDownEnabled = ko.observable(false);
        self.layerUpEnabled = ko.observable(false);

        var BoxWidth;
        var BoxHeight;
        var centerX;
        var centerY;
        var selectedLayer;
        var gcodeCoords;
        var camCoords;

        //white placeholder images
        document.getElementById('headCameraImage').setAttribute( 'src', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3wMRCQAfAmB4CgAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAAAMSURBVAjXY/j//z8ABf4C/tzMWecAAAAASUVORK5CYII=');


        // // This will get called before the ViewModel gets bound to the DOM, but after its depedencies have
        // // already been initialized. It is especially guaranteed that this method gets called _after_ the settings
        // // have been retrieved from the OctoPrint backend and thus the SettingsViewModel been properly populated.
        // self.onBeforeBinding = function() {
        //     _cameraGrid = new camGrid(BoxWidth,BoxHeight,centerX,centerY,selectedLayer,gcodeCoords,camCoords,_cameraGridCanvas);
        //     _cameraGridCanvas.addEventListener("click", self.onSmdTrayClick, false); //"click, dblclick"
        //     _cameraGridCanvas.addEventListener("dblclick", self.onSmdTrayDblclick, false); //"click, dblclick"
        // };

        function _redrawObjects(){
            _cameraGrid.erase();
            _cameraGrid.drawGCodeLines();
            _cameraGrid.drawCameragrid();
            _cameraGrid.drawCameraPathLines();
        }

        function _centerObjects(){
          _cameraGrid.arrangeObjects();
        }

        function _updateLayerHeader(){
          self.CamGridHeader("Camera lookup grid on Layer: " + (selectedLayer + 1));
        }

        self.incrementLayer = function() {
            selectedLayer += 1;
            // Update selected Layer in cameragrid thenredraw everything
            _cameraGrid.setCurrentLayer(selectedLayer);
            _redrawObjects();
            _updateLayerHeader();

            self.layerDownEnabled(selectedLayer > 0);
            self.layerUpEnabled(selectedLayer < gcodeCoords.length-1);
        };

        self.decrementLayer = function() {
            selectedLayer -= 1;
            // Update selected Layer in cameragrid thenredraw everything
            _cameraGrid.setCurrentLayer(selectedLayer);
            _redrawObjects();
            _updateLayerHeader();

            self.layerDownEnabled(selectedLayer > 0);
            self.layerUpEnabled(selectedLayer < gcodeCoords.length-1);
        };

        self.onTabChange = function(current, previous) {
            self.tabActive = current == "#tab_plugin_OctoCamDox";
            if (self.tabActive && (selectedLayer != undefined)) {
                // self.loadFile(self.selectedFile.path(), self.selectedFile.date());
                _cameraGrid.reDrawLayer(selectedLayer);
                _cameraGrid.drawCameragrid(selectedLayer);
            }
        };

       self.onDataUpdaterPluginMessage = function(plugin, data) {
          if(plugin == "OctoCamDox") {
              if(data.event == "FILE") {
                  if(data.data.hasOwnProperty("cameraCoordinates")) {
                      self.stateString("Succesfully created and loaded Camera Grid from GCode");
                      //initialize the the data
                        selectedLayer = 0;
                        BoxWidth = data.data.CamPixelResX;
                        BoxHeight = data.data.CamPixelResY;
                        infoList = JSON.parse(data.data.gridInfoList);
                        gcodeCoords = JSON.parse(data.data.gcodeCoordinates);
                        camCoords = JSON.parse(data.data.cameraCoordinates);
                        _cameraGrid = new camGrid(BoxWidth,BoxHeight,infoList,selectedLayer,gcodeCoords,camCoords,_cameraGridCanvas);

                        // _cameraGrid.erase();
                        _cameraGrid.setCurrentLayer(selectedLayer);
                        _centerObjects();
                        _redrawObjects();
                        _updateLayerHeader();

                        if (selectedLayer == undefined) {
                            self.layerDownEnabled(false);
                            self.layerUpEnabled(false);
                        }
                        if (selectedLayer != undefined) {
                            self.layerDownEnabled(false);
                            self.layerUpEnabled(gcodeCoords.length-1 > 0);
                        }
            		      }
                  //Set used camera resoiuton
                  if(data.data.hasOwnProperty("CamPixelResX") && data.data.hasOwnProperty("CamPixelResY")) {
                    var width = data.data.CamPixelResX;
                    var height = data.data.CamPixelResY;
                    self.cameraResolution(width + "x" + height);
                    }
                  }
                  else if(data.event == "OPERATION") {
                      self.currentOperation(data.data.type + " part nr " + data.data.part);
                  }
                  else if(data.event == "ERROR") {
                      self.stateString("ERROR: \"" + data.data.type + "\"");
                      if(data.data.hasOwnProperty("part")) {
                          self.stateString(self.StateString + "appeared while processing part nr " + data.data.part);
                      }
                  }
                  else if(data.event == "INFO") {
                      self.stateString("INFO: \"" + data.data.type + "\"");
                  }
                  else if(data.event == "HEADIMAGE") {
                      document.getElementById('headCameraImage').setAttribute( 'src', data.data.src );
                  }
              //self.debugvar("Plugin = OctoCamDox");
          }
      };
    }

    // This is how our plugin registers itself with the application, by adding some configuration information to
    // the global variable ADDITIONAL_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push({
        // This is the constructor to call for instantiating the plugin
        construct: OctoCamDoxViewModel,
        // This is a list of dependencies to inject into the plugin, the order which you request here is the order
        // in which the dependencies will be injected into your view model upon instantiation via the parameters
        // argument
        dependencies: ["settingsViewModel", "controlViewModel", "connectionViewModel"],
        // Finally, this is the list of all elements we want this view model to be bound to.
        elements: ["#tab_plugin_OctoCamDox"]
    });
});
