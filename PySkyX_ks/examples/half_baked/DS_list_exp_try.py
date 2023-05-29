#!/usr/bin/env python3
#

# Ken Sturrock
# June 5, 2021

from library.PySkyX_ks import *

import sys
import os
import math
import statistics
import time

uniqueTargSet = set()

initialFocused = "No"

defaultExposure = "10"


def adjExposure(origExp, XCoord, YCoord):
    if TSXSend("ccdsoftCamera.ImageReduction") != "0":
    
        writeNote("Measuring exposure.")
        
        newXCoord = float(TSXSend('ccdsoftCamera.BinX')) * float(XCoord)  
        newYCoord = float(TSXSend('ccdsoftCamera.BinY')) * float(YCoord)
        
        boxSizeVert = int(float(TSXSend("ccdsoftCamera.TrackBoxY")) / 2)
        boxSizeHoriz = int(float(TSXSend("ccdsoftCamera.TrackBoxX")) / 2)
        
        newTop = int(newYCoord - boxSizeVert)
        newBottom = int(newYCoord + boxSizeVert)
        newLeft = int(newXCoord - boxSizeHoriz)
        newRight = int(newXCoord + boxSizeHoriz)
        
        TSXSend("ccdsoftCamera.SubframeTop = " + str(newTop))
        TSXSend("ccdsoftCamera.SubframeLeft = " + str(newLeft))
        TSXSend("ccdsoftCamera.SubframeBottom = " + str(newBottom))
        TSXSend("ccdsoftCamera.SubframeRight = " + str(newRight))
        TSXSend("ccdsoftCamera.Subframe = true")
        TSXSend("ccdsoftCamera.Delay = 1")
        TSXSend("ccdsoftCamera.AutoSaveOn = false")
        TSXSend("ccdsoftCamera.ExposureTime = " + origExp)
        
        TSXSend("ccdsoftCamera.TakeImage()")
       
        imageDepth = 16

        fullWell = math.pow (2, int(imageDepth))
        brightestPix = TSXSend("ccdsoftCamera.MaximumPixel")
        brightness = round((int(brightestPix) / int(fullWell)), 2)
        writeNote("Brightness: " + str(brightness))
    
        if brightness >= 0.2 and brightness <= 0.75:
            writeNote("No exposure change recommended.")
            return str(origExp)
    
        else:
            units = brightness / float(origExp)
        
            if brightness > 0.75:
                writeNote("Star too bright.")
    
                while brightness > 0.80:
    
                    origExp = float(origExp) / 2
                    TSXSend("ccdsoftCamera.ExposureTime = " + str(origExp))
                    TSXSend("ccdsoftCamera.TakeImage()")
                    fullWell = math.pow (2, int(imageDepth))
                    brightestPix = TSXSend("ccdsoftCamera.MaximumPixel")
                    brightness = round((int(brightestPix) / int(fullWell)), 2)
                    writeNote("Exposure: " + str(origExp) + " Brightness: " + str(brightness))
    
                    units = brightness / float(origExp)
    
                newExp = 0.75 / units
    
            if brightness < 0.2:
                newExp = 0.5 / units
        
            newExp = round(newExp, 1)
        
            if newExp > (float(origExp) * 1.5):
                newExp = (float(origExp) * 1.5)

            if newExp < 5:
                newExp = 5
        
            writeNote("Recommend exposure of " + str(newExp) + ".")
            return str(newExp) 
    else:
        writeNote("Exposure not adjusted because guider is not calibrated.")
        return str(origExp)
 
def qClassicIL():
    TSXSend("ccdsoftCameraImage.AttachToActiveImager()")

    TSXSend("ImageLink.pathToFITS = ccdsoftCameraImage.Path")

    FITSPath = TSXSend("ccdsoftCameraImage.Path")
    ILPath = TSXSend("ImageLink.pathToFITS")

    writeNote("FITs Path: " + FITSPath)
    writeNote("IL Path:   " + ILPath)

    if "fit" not in FITSPath:
        print("FIT mystery:")

        print(TSXSend("ccdsoftCamera.Asynchronous"))
        print(TSXSend("ccdsoftCamera.AutoSaveOn"))
        print(TSXSend("ccdsoftCamera.Frame"))
        print(TSXSend("ccdsoftCamera.Subframe"))
        print(TSXSend("ccdsoftCamera.Delay"))
        print(TSXSend("ccdsoftCamera.ExposureTime"))



    FITSProblem = "No"


    if TSXSend("ccdsoftCameraImage.ImageUseDigitizedSkySurvey") == "1":
        FITSProblem = "Yes"
        
    else:

        if "undefined" in str(TSXSend('ccdsoftCameraImage.FITSKeyword("FOCALLEN")')):
            FITSProblem = "Yes"

        if "250" in str(TSXSend('ccdsoftCameraImage.FITSKeyword("FOCALLEN")')):
            FITSProblem = "Yes"
    
        if "250" in str(TSXSend('ccdsoftCameraImage.FITSKeyword("XPIXSZ")')):
            FITSProblem = "Yes"
    
    if FITSProblem == "Yes":
        ImageScale = 1.70                                               
        TSXSend("ImageLink.unknownScale = 1")

    else: 
        FocalLength = TSXSend('ccdsoftCameraImage.FITSKeyword("FOCALLEN")')
        PixelSize =  TSXSend('ccdsoftCameraImage.FITSKeyword("XPIXSZ")')
        Binning =  TSXSend('ccdsoftCameraImage.FITSKeyword("XBINNING")')

        ImageScale = ((float(PixelSize) * float(Binning)) / float(FocalLength) ) * 206.3

        ImageScale = round(float(ImageScale), 2)

    TSXSend("ImageLink.scale = " + str(ImageScale))

    ilResults = TSXSend("ImageLink.execute()")

    newIS = TSXSend("ImageLinkResults.imageScale")

    TSXSend("ImageLink.scale = " + str(newIS))

    TSXSend("ImageLink.unknownScale = 0")

    TSXSend("ccdsoftCameraImage.ScaleInArcsecondsPerPixel = " + str(newIS))         

    return ilResults


def shootInitialImage():
    TSXSend("ccdsoftCamera.Asynchronous = false")
    TSXSend("ccdsoftCamera.AutoSaveOn = true")
    TSXSend("ccdsoftCamera.Frame = 1")
    TSXSend("ccdsoftCamera.Subframe = false")
    TSXSend("ccdsoftCamera.Delay = 5")
    TSXSend("ccdsoftCamera.ExposureTime = " + defaultExposure)

    camMesg = TSXSend("ccdsoftCamera.TakeImage()") 

    TSXSend("ccdsoftCamera.Delay = 0")

    if "Process aborted." in camMesg:
        timeStamp("Script Aborted.")
        sys.exit()

def getTargCoords(target):
    result = TSXSend('sky6StarChart.Find("' + target + '")')
    if ("rror"  in result) or ("not found" in result):
        timeStamp(target + " not found. Correct catalog activated?")

        return "Fail"

    TSXSend("sky6ObjectInformation.Index = 0")

    TSXSend("sky6ObjectInformation.Property(56)")				
    targRA = TSXSend("sky6ObjectInformation.ObjInfoPropOut")	
    TSXSend("sky6ObjectInformation.Property(57)")			
    targDec = TSXSend("sky6ObjectInformation.ObjInfoPropOut")

    TSXSend("ccdsoftCameraImage.RADecToXY(" + targRA + ", " + targDec + ")")

    targX = round(float(TSXSend("ccdsoftCameraImage.RADecToXYResultX()")),3)
    targY = round(float(TSXSend("ccdsoftCameraImage.RADecToXYResultY()")),3)

    targRA = float(targRA)
    targDec = float(targDec)

    if (targX == 0.0) or (targY == 0.0):
        writeError("X & Y Results are zero.")
        print("           Something may be wrong with the image or SkyX.")
        print("           Maybe, SkyX is using old Image Link data.")
        print("           If image is OK, try a restart.")
        return "Fail"

    imageWidth = float(TSXSend("ccdsoftCameraImage.WidthInPixels"))
    imageHeight = float(TSXSend("ccdsoftCameraImage.HeightInPixels"))

    if (targX >= imageWidth) or \
            (targX < 0):
                writeError("Target location exceeds supplied image boundries.")
                return "Fail"

    if (targY >= imageHeight) or \
            (targY < 0):
                writeError("Target location exceeds supplied image boundries.")
                return "Fail"

    lsXRaw = TSXSend("ccdsoftCameraImage.InventoryArray(0)")
    lsYRaw = TSXSend("ccdsoftCameraImage.InventoryArray(1)")
    targFWHMRaw = TSXSend("ccdsoftCameraImage.InventoryArray(4)")
            
    lsXArray = lsXRaw.split(",")
    lsYArray = lsYRaw.split(",")
    targFWHMArray = targFWHMRaw.split(",")

    smallestDist = imageHeight / 2
    cLS = 0

    for LS in range(len(lsXArray)):
        distX = float(lsXArray[LS]) - targX
        distY = float(lsYArray[LS]) - targY
        pixDist = math.sqrt((distX * distX) + (distY * distY))
        if pixDist < smallestDist:
            cLS = LS
            smallestDist = pixDist

    targX = lsXArray[cLS]
    targY = lsYArray[cLS]
 
    return [targX, targY, targRA, targDec, cLS]


def imageStar():
    for loop in range(5):

        TSXSend("ccdsoftCamera.Asynchronous = false")
        TSXSend("ccdsoftCamera.AutoSaveOn = true")
        TSXSend("ccdsoftCamera.Frame = 1")
            
        TSXSend("ccdsoftCamera.Subframe = false")
        TSXSend("ccdsoftCamera.Delay = 5")
    
        timeStamp("Shooting image " + str(loop) + ".")
    
        camMesg = TSXSend("ccdsoftCamera.TakeImage()") 
    
        TSXSend("ccdsoftCamera.Delay = 0")

        if "Process aborted." in camMesg:
            timeStamp("Script Aborted.")
            sys.exit()

        if camMesg == "0":
            TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
            TSXSend("ccdsoftCameraImage.ShowInventory()")
            starsFound = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")
        
            dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
            orgImgName = os.path.splitext(fileName)[0]
            if os.path.exists(dirName + "/" + orgImgName + ".SRC"):
                writeNote("Deleting light source file.")
                os.remove(dirName + "/" + orgImgName + ".SRC")

            if os.path.exists(dirName + "/" + orgImgName + "Uncalibrated.fit"):
                writeNote("Deleting uncalibrated image.")
                os.remove(dirName + "/" + orgImgName + "Uncalibrated.fit")    

            if os.path.exists(dirName + "/" + orgImgName + "NoAutoDark.fit"):
                writeNote("Deleting no-AutoDark image.")                
                os.remove(dirName + "/" + orgImgName + "NoAutoDark.fit")  
            
            if  int(starsFound) < 10:
                writeNote("There are only " + starsFound + " light sources in image.")
                if os.path.exists(dirName + "/" + orgImgName + ".fit"):
                    writeNote("Deleting low-star count image.")
                    os.remove(dirName + "/" + orgImgName + ".fit")


                defFilter = TSXSend("ccdsoftCamera.FilterIndexZeroBased")
                cloudWait(defFilter)
    
        else:
            timeStamp("ERROR: " + camMesg)
            return "Fail"


def dsFocus(target):
    if targHA(target) < 0.75 and targHA(target) > -0.75:
        writeNote("Target is near the meridian.")
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
            if TSXSend("sky6RASCOMTele.DoCommandOutput") == "1":
                TSXSend('sky6RASCOMTele.Jog(420, "E")')
                writeNote("OTA is west of the meridian pointing east.")
                writeNote("Slewing towards the east, away from meridian.")

            else:
                TSXSend('sky6RASCOMTele.Jog(420, "W")')
                writeNote("OTA is east of the meridian, pointing west.")
                writeNote("Slewing towards the west, away from meridian.")


            if "Temma" in TSXSend("SelectedHardware.mountModel"):
                TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")
                writeNote("Resetting Temma tracking rate.")

 
    if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        timeStamp("@Focus2 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))
        return "Success"

    else:  
        result = TSXSend("ccdsoftCamera.AtFocus2()")

        if "Process aborted." in result:
            timeStamp("Script Aborted.")
            sys.exit()

        if "Error" in result:
            timeStamp("@Focus2 failed: " + result)
            return "Fail"
        else:

            TSXSend("sky6ObjectInformation.Property(0)")
            TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            
            timeStamp("@Focus2 success.  Position = " + TSXSend("ccdsoftCamera.focPosition") + ". Star = " \
                    + TSXSend("sky6ObjectInformation.ObjInfoPropOut"))
            return "Success"

def chkTarget(target):
    if targExists(target) == "No":
        print("    ERROR: " + target + " not found in SkyX database.")
        return "Fail"

    if str(TSXSend("SelectedHardware.mountModel")) ==  "Telescope Mount Simulator":
        writeNote("Running on simulated mount.")
        return "Success"

    altLimit = 35

    isDayLight()

    currentHA = targHA(target)
    currentAlt = targAlt(target) 
    currentAz = targAz(target)

    if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
        if currentAlt < 55 and currentHA < 0 and currentAz < 80:
            writeNote('Target is in "star-eating tree" zone. Skipping.')
            time.sleep(5)
            return "Fail"

    if currentAlt < altLimit and currentHA > 0:
        timeStamp("Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
        timeStamp("Target " + target + " has sunk too low.")
        return "Fail"

    if currentAlt < altLimit and currentHA < 0:
        writeNote("Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
        writeNote("Target " + target + " is still too low.")
        return "Fail"

    return "Success"



##### Start of actual program ######

if (len(sys.argv) == 1):
    timeStamp("ERROR. Please specify list of target names to process.")
    sys.exit()

fileName = sys.argv[1]
newPathName = flipPath(fileName)

print("Processing: " + newPathName)

if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
    if str(TSXSend("SelectedHardware.cameraModel")) == "QSI Camera  ":
        writeNote("Setting up Ken's QSI camera defaults.")
        TSXSend("ccdsoftCamera.TemperatureSetPoint = -10")
        TSXSend("ccdsoftCamera.RegulateTemperature = true")
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = 1")
        TSXSend("ccdsoftAutoguider.ImageReduction = 1")
        TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Faster Image Downloads")')

with open(newPathName) as starNameFile:
    starList = starNameFile.readlines()

starList = [line.rstrip() for line in starList]

for star in starList:
    if ("Object" not in star):
        uniqueTargSet.add(star)

uniqueTargSet = sorted(uniqueTargSet, key=starList.index)

starList = list(uniqueTargSet)

for index in range(len(starList)):
    starList[index] = " ".join(starList[index].split())

total = len(starList)

writeNote("Found " + str(total) + " unique target names.")

for index,star in enumerate(starList):

    print("----------")
    timeStamp("Processing: " + star + " (" + str(index + 1) + " of " + str(total) + ")")
    print("----------")

    result = chkTarget(star)

    if result == "Success":

        if (index % 15 == 0) or (initialFocused == "No"):
            writeNote("Attempting to focus.")
            slew(star)
            result = dsFocus(star)
            if result != "Success":
                print("Focus failed!")
                softPark()
            initialFocused = "Yes"

        slew(star)
        shootInitialImage()
        ilResults = qClassicIL()

        if ("rror:" in ilResults) or ("Fail" in ilResults):
            writeError("Image Link Failed.")
            writeError("" + ilResults)

    
        else:
            timeStamp("Image Link Successful.")
            TSXSend("ccdsoftCameraImage.InsertWCS()")
    
            results = getTargCoords(star)

            dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
            orgImgName = os.path.splitext(fileName)[0]
            if os.path.exists(dirName + "/" + orgImgName + ".SRC"):
                writeNote("Deleting light source file.")
                os.remove(dirName + "/" + orgImgName + ".SRC")
    
            if os.path.exists(dirName + "/" + orgImgName + "Uncalibrated.fit"):
                writeNote("Deleting uncalibrated analysis image.")
                os.remove(dirName + "/" + orgImgName + "Uncalibrated.fit")  
    
            if os.path.exists(dirName + "/" + orgImgName + "NoAutoDark.fit"):
                writeNote("Deleting no-AutoDark analysis image.")
                os.remove(dirName + "/" + orgImgName + "NoAutoDark.fit")  
    
            if os.path.exists(dirName + "/" + orgImgName + ".fit"):
                writeNote("Deleting analysis image.")
                os.remove(dirName + "/" + orgImgName + ".fit")
    
            targX = results[0]
            targY = results[1]
    
            newExposure = adjExposure(defaultExposure, targX, targY)
        
            TSXSend("ccdsoftCamera.ExposureTime = " + str(newExposure))
    
            imageStar()


softPark()

