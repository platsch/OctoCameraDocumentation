function camGrid(width, height, centerX, centerY, currentSelectedLayer, GCodeCoordinates, cameraCoordinates, canvas){
		var self = this;

		var _width = width;
    var _height= height;
		var _centerX = centerX;
		var _centerY = centerY;
		var _currentSelectedLayer = currentSelectedLayer;
		var _GCodeCoordinates = GCodeCoordinates;
		var _cameraCoordinates = cameraCoordinates;
		var _trayCanvas = canvas;


    self.erase = function() {
        _drawTray();
    };

		self.drawPrintables = function() {
			console.log("Draw Printables entered")
			console.log("Resolution of the Cam box is width: " + _width + " height was: " + _height)
			console.log("First GCode coordinate X: " + _GCodeCoordinates[0][0][0] + " Y: " + _GCodeCoordinates[0][0][0])
				// _drawPrintables();
		}

	function _drawGCodeLines () {
		if (_trayCanvas && _trayCanvas.getContext) {
	      var ctx = _trayCanvas.getContext("2d");
				var i = o
				while (i < _GCodeCoordinates.length-1){
					ctx.beginPath();
					ctx.moveTo(_GCodeCoordinates[i][0], _GCodeCoordinates[i][1]);
					ctx.lineTo(_GCodeCoordinates[i+1][0],_GCodeCoordinates[i+1][1]);
					ctx.stroke();
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

				for(var x=0; x<_width; x++) {
                    for(var y=0; y<_height; y++) {
                        _drawTrayBox(x+1, y+1, canvasBoxSize);
                    }
                }
            }
        }
	}

    // draw a single tray box
    function _drawTrayBox(col, row, size) {
        col -=1;
        row -=1;
        if (_trayCanvas && _trayCanvas.getContext) {
            var ctx = _trayCanvas.getContext("2d");
            if (ctx) {
                ctx.lineWidth = 4;
                ctx.strokeStyle = "green";
                ctx.fillStyle = "white";
                ctx.strokeRect (col*size+ctx.lineWidth/2,(_height-1)*size-row*size+ctx.lineWidth/2,size-ctx.lineWidth/2,size-ctx.lineWidth/2);
                ctx.fillRect (col*size+ctx.lineWidth,(_height-1)*size-row*size+ctx.lineWidth,size-ctx.lineWidth,size-ctx.lineWidth);
            }
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
                boxSize = Math.min((size_x-4)/_width, (size_y-4)/_height);
            }
        }
        return Math.floor(boxSize);
    }
}
