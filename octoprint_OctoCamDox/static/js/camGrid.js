function camGrid(width, height, infoList, currentSelectedLayer, GCodeCoordinates, cameraCoordinates, canvas){
		var self = this;

		var _camBoxWidth = width;
    var _camBoxHeight= height;
		var _centerX = infoList[currentSelectedLayer][4];
		var _centerY = infoList[currentSelectedLayer][5];
		var _minX = infoList[currentSelectedLayer][1];
		var _minY = infoList[currentSelectedLayer][3];
		var _maxX = infoList[currentSelectedLayer][0];
		var _maxY = infoList[currentSelectedLayer][2];
		var _currentSelectedLayer = currentSelectedLayer;
		var _GCodeCoordinates = GCodeCoordinates;
		var _cameraCoordinates = cameraCoordinates;
		var _trayCanvas = canvas;


    self.erase = function() {
        _drawWhiteBox();
    };

		self.drawPrintables = function() {
			// console.log("Draw Printables entered")
			// console.log("Resolution of the Cam box is width: " + _camBoxWidth + " height was: " + _camBoxHeight)
			// console.log("First GCode coordinate X: " + _GCodeCoordinates[0][0][0] + " Y: " + _GCodeCoordinates[0][0][0])
			_drawGCodeLines (_currentSelectedLayer);
		}

		self.drawGCodeLines = function(inputLayer) {
			_drawGCodeLines (inputLayer);
		}

		self.drawCameragrid = function(inputLayer) {
			_drawCamGrid(inputLayer);
		}

		self.drawCenterCircle = function(){
			_drawCenterCircle();
		}

		self.arrangeObjects = function() {
			_zoomDrawnObjects();
		}

	function _drawGCodeLines (inputLayer) {
		var ctx = _trayCanvas.getContext("2d");
		if (_trayCanvas && _trayCanvas.getContext) {
				for (var i = 0 ; i < _GCodeCoordinates[inputLayer].length-1 ; ++i){
					ctx.save();
					var x = ctx.canvas.width/2;
					var y = ctx.canvas.height/2;
					ctx.translate(-_centerX, -_centerY);
					ctx.translate(x, y);

					ctx.strokeStyle = "black";
					ctx.beginPath();
					ctx.moveTo(_GCodeCoordinates[inputLayer][i][0], _GCodeCoordinates[inputLayer][i][1]);
					ctx.lineTo(_GCodeCoordinates[inputLayer][i+1][0], _GCodeCoordinates[inputLayer][i+1][1]);
					ctx.stroke();
					ctx.restore();
			}
		}
	}

	function _drawWhiteBox() {
		if (_trayCanvas && _trayCanvas.getContext) {
            var ctx = _trayCanvas.getContext("2d");
            if (ctx) {
                var size_x = ctx.canvas.width;
                var size_y = ctx.canvas.height;
                var canvasBoxSize = _getCanvasBoxSize();

                //initialize white tray
                ctx.fillStyle = "white";
                ctx.fillRect(0,0,size_x,size_y);
                // ctx.strokeRect (0,0,size_x,size_y);
							}
					}
	}

	function _drawTray () {
		if (_trayCanvas && _trayCanvas.getContext) {
            var ctx = _trayCanvas.getContext("2d");
            if (ctx) {
                var size_x = ctx.canvas.width;
                var size_y = ctx.canvas.height;
                var canvasBoxSize = _getCanvasBoxSize();

                //initialize white tray
                ctx.strokeStyle = "black";
                ctx.fillStyle = "white";
                ctx.lineWidth = 1;
                ctx.fillRect(0,0,size_x,size_y);
                ctx.strokeRect (0,0,size_x,size_y);

				for(var x=0; x<_camBoxWidth; x++) {
                    for(var y=0; y<_camBoxHeight; y++) {
                        _drawGridBox(x+1, y+1, canvasBoxSize);
                    }
                }
            }
        }
	}

    // draw a single grid box
    function _drawGridBox(x, y) {
        if (_trayCanvas && _trayCanvas.getContext) {
            var ctx = _trayCanvas.getContext("2d");
            if (ctx) {
								ctx.save();
								var posx = ctx.canvas.width/2;
								var posy = ctx.canvas.height/2;
								ctx.translate(-_centerX, -_centerY);
								ctx.translate(posx, posy);

                ctx.lineWidth = 1;
                ctx.strokeStyle = "green";
                // ctx.fillStyle = "white";
                ctx.strokeRect (x-(_camBoxWidth/2),y-(_camBoxHeight/2),_camBoxWidth,_camBoxHeight);
                // ctx.fillRect (width*size+ctx.lineWidth,(_camBoxHeight-1)*size-height*size+ctx.lineWidth,size-ctx.lineWidth,size-ctx.lineWidth);
								ctx.restore();
            }
        }
    }

		function _drawCamGrid(inputLayer) {
			for (var i = 0 ; i < _cameraCoordinates[inputLayer].length ; ++i){
				_drawGridBox(_cameraCoordinates[inputLayer][i][0], _cameraCoordinates[inputLayer][i][1]);
			}
		}

    // returns the box size to use the available canvas-space in an optimal way
    function _getCanvasBoxSize() {
        var boxSize = 0;
        if (_trayCanvas && _trayCanvas.getContext) {
            var ctx = _trayCanvas.getContext("2d");
            if (ctx) {
                var size_x = ctx.canvas.width;
                var size_y = ctx.canvas.height;
                boxSize = Math.min((size_x-4)/_camBoxWidth, (size_y-4)/_camBoxHeight);
            }
        }
        return Math.floor(boxSize);
    }

		function _centerDrawnObjects(){
			if (_trayCanvas && _trayCanvas.getContext) {
					var ctx = _trayCanvas.getContext("2d");
					// Move object into center of Canvas
					var x = ctx.canvas.width/2;
					var y = ctx.canvas.height/2;

					ctx.translate(-centerX, -centerY);
					ctx.translate(x, y);
			}
		}

		function _zoomDrawnObjects(){
			if (_trayCanvas && _trayCanvas.getContext) {
					var ctx = _trayCanvas.getContext("2d");

					var x = ctx.canvas.width/2;
					var y = ctx.canvas.height/2;

					// TODO: Zoomfactor should be calculated dynamically
					// Zoom object
					ctx.translate(x, y);

					// Make the necessary transformations for the zoom
					var width = _maxX - _minX;
					var length = _maxY - _minY;
					var scaleF = width > length ? (x - _camBoxWidth) / width : (y - _camBoxHeight) / length;
					var factor = scaleF;
					ctx.scale(factor,factor);

					ctx.translate(-x, -y);
				}
		}

		function _drawCenterCircle(){
			if (_trayCanvas && _trayCanvas.getContext) {
					var ctx = _trayCanvas.getContext("2d");

					var x = ctx.canvas.width/2;
					var y = ctx.canvas.height/2;

					ctx.beginPath();
					ctx.fillStyle = "black";
					ctx.arc(0,0,3,0,(Math.PI*2),true);
					ctx.fill();
					// ctx.stroke();
				}
		}
}
