/* Java Script */

var camera = "$0";      //Imager or guider
var expT = $1;  // Exposure time in seconds
var delay = $2;
var filterNum = $3;
var bin = $4;

if (camera == "Imager"){
    if (SelectedHardware.filterWheelModel != "<No Filter Wheel Selected>"){
        ccdsoftCamera.filterWheelConnect();
        if (filterNum != "NA"){
            ccdsoftCamera.FilterIndexZeroBased = filterNum;
        }
    }
}

if (camera == "Imager"){

    ccdsoftCamera.Asynchronous = false;
    ccdsoftCamera.AutoSaveOn = true;
    ccdsoftCamera.Subframe = false;
    ccdsoftCamera.ExposureTime = expT;
    ccdsoftCamera.BinX = ccdsoftCamera.BinY = bin;
    ccdsoftCamera.ImageReduction = 0;
    if (delay != "NA"){
        ccdsoftCamera.Delay = delay;
    }

// Image reduction here?
    ccdsoftCamera.TakeImage();
    var camMesg = ccdsoftCamera.IsExposureComplete;
    while (camMesg == '0'){camMesg = ccdsoftCamera.IsExposureComplete;}

    if (camMesg != 1){console.log('WARNING : Failure to take image'); out = ""}
    else{
        ccdsoftCameraImage.AttachToActiveImager();
        var out = ccdsoftCamera.LastImageFileName;
    }
}
if (camera == "Guider"){
    ccdsoftAutoguider.Asynchronous = false;
    ccdsoftAutoguider.AutoSaveOn = true;
    ccdsoftAutoguider.Frame = 1;
    ccdsoftAutoguider.Subframe = false;
    ccdsoftAutoguider.ExposureTime = expT;
    ccdsoftAutoguider.BinX = ccdsoftAutoguider.BinY = bin;
    ccdsoftAutoguider.ImageReduction = 0;
    if (delay != "NA"){
        ccdsoftAutoguider.Delay = delay;
    }

    ccdsoftAutoguider.TakeImage()
    var camMesg = ccdsoftAutoguider.IsExposureComplete;

    while (camMesg == '0'){camMesg = ccdsoftAutoguider.IsExposureComplete;}

    if (camMesg != 1){console.log('WARNING : Failure to take image'); out = ""}
    else{
        ccdsoftAutoguiderImage.AttachToActiveAutoguider();
        var out = ccdsoftAutoguider.LastImageFileName;
    }
}
out =out;