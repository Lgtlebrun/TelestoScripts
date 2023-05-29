#!/usr/bin/env python3

#
# Script to image a list of double stars (or other targets). The input list should be a single column 
# and the targets recognizeable by SkyX's "find".
#
# You will specify the file name as the command line argument. 
#
# Ken Sturrock
# December 16, 2022
#



######################################################################################
# Set these five variables for your needs ############################################
######################################################################################

# How many images to take for each target?
numImages = 10 

# How long of an exposure at each target? Note the quotes.
targExposure = "10"

# Which focus routine to use? Must be a number. 2 = @Focus2, 3 = @Focus3, 0 (or other) = no-focus.
# Note that if @F2 fails, it will roll over and try @F3.
focusStyle = 2 

# Which style of slewing? "CLS" uses a closed loop slew. "regular" (or other) relies on the mount's pointing. 
# Note the quotes.
slewStyle = "regular"

# How many targets between focuses?
focusAfter = 10

######################################################################################
# Leave everything below this alone ##################################################
######################################################################################


from library.PySkyX_ks import *

import time
import sys
import os

initialFocused = "No"
uniqueTargSet = set()


def chkTarget(target):
#
# This is a modified version of the routine from run_target-2.
#
# It makes sure that the target is valid & up and that the sky is dark.
#
#

    if targExists(target) == "No":
        print("    ERROR: " + target + " not found in SkyX database.")
        return "Fail"

    # If you're on the simulator, you're probably debugging during the day.
    if str(TSXSend("SelectedHardware.mountModel")) ==  "Telescope Mount Simulator":
        writeNote("Running on simulated mount.")
        return "Success"

    altLimit = 35

    # If light outside then wait or pack it in.
    isDayLight()

    currentHA = targHA(target)
    currentAlt = targAlt(target) 
    currentAz = targAz(target)

    #
    # This code is to handle my neighbor's giant tree
    #
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


def imageStar(target):
#
# DS alternative to regular takeImage
#

    if (slewStyle != "CLS"):
        slew(target)
    else:
        CLSlew(target, "0")

    for loop in range(numImages):

        TSXSend("ccdsoftCamera.Asynchronous = false")
        TSXSend("ccdsoftCamera.AutoSaveOn = true")
        TSXSend("ccdsoftCamera.Frame = 1")
        TSXSend("ccdsoftCamera.Subframe = false")
        TSXSend("ccdsoftCamera.Delay = 5")
        TSXSend("ccdsoftCamera.ExposureTime = " + targExposure)

        timeStamp("Shooting image " + str(loop) + ".")

        camMesg = TSXSend("ccdsoftCamera.TakeImage()") 

        # Resetting this in case we have run a focus next.
        TSXSend("ccdsoftCamera.Delay = 0")

        if "Process aborted." in camMesg:
            timeStamp("Script Aborted.")
            sys.exit()

        if camMesg == "0":
        #
        # Results from the camera are normal. Check if there are any stars.
        #
            TSXSend("ccdsoftCameraImage.AttachToActiveImager()")
            TSXSend("ccdsoftCameraImage.ShowInventory()")
            starsFound = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")
    
            dirName,fileName = os.path.split(TSXSend("ccdsoftCameraImage.Path"))
            
            orgImgName = os.path.splitext(fileName)[0]

            if os.path.exists(dirName + "/" + orgImgName + ".SRC"):
                os.remove(dirName + "/" + orgImgName + ".SRC")
        
            if  int(starsFound) < 10:
                writeNote("There are only " + starsFound + " light sources in image.")
                if os.path.exists(dirName + "/" + orgImgName + ".fit"):
                    writeNote("Deleting image.")
                    os.remove(dirName + "/" + orgImgName + ".fit")
                cloudWait()

        else:
            timeStamp("ERROR: " + camMesg)
            softPark()
    

def dsFocus(target):
#
# Figure out our focus options.
#



    if (focusStyle == 2):
    # 
    # Are we using @F2?
    #

        if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        #
        # Are we using the camera simulator? If so, just lie about it and exit.
        #
            timeStamp("@Focus2 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))
            return "Success"


        if targHA(target) < 0.75 and targHA(target) > -0.75:
        # This joyfulness slews the mount away from the meridian so that the @F2 database
        # doesn't find a focusing star on the wrong side of the meridian which can cause
        # multiple meridian flips.
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

        result = TSXSend("ccdsoftCamera.AtFocus2()")
    
        if "Process aborted." in result:
            timeStamp("Script Aborted.")
            sys.exit()

        if "Error" in result:
            timeStamp("@Focus2 failed: " + result)

            timeStamp("Trying @Focus3")

            result = TSXSend("ccdsoftCamera.AtFocus3(3, true)")

            if "Process aborted." in result:
                timeStamp("Script Aborted.")
                sys.exit()

            if "Error" in result:
                timeStamp("@Focus3 also failed: " + result)
                return "Fail"
            else:
                timeStamp("@Focus3 success.  Position = " + TSXSend("ccdsoftCamera.focPosition") )
                return "Success"

        else:
    
            TSXSend("sky6ObjectInformation.Property(0)")
            TSXSend("sky6ObjectInformation.ObjInfoPropOut")
                
            timeStamp("@Focus2 success.  Position = " + TSXSend("ccdsoftCamera.focPosition") + ". Star = " \
                + TSXSend("sky6ObjectInformation.ObjInfoPropOut"))
            return "Success"

    else:
    #
    # We're using @F3.
    #
        if TSXSend("ccdsoftCamera.ImageUseDigitizedSkySurvey") == "1":
        #
        # Are we using the camera simulator? If so, just lie about it and exit.
        #
            timeStamp("@Focus3 success (simulated). Position = " + TSXSend("ccdsoftCamera.focPosition"))
            return "Success"


        result = TSXSend("ccdsoftCamera.AtFocus3(3, true)")

        if "Process aborted." in result:
            timeStamp("Script Aborted.")
            sys.exit()

        if "Error" in result:
            timeStamp("@Focus3 failed: " + result)
            return "Fail"
        else:
            timeStamp("@Focus3 success.  Position = " + TSXSend("ccdsoftCamera.focPosition") )
            return "Success"







######################################################################################
# Start of actual program ############################################################
######################################################################################

#
# Read through the command line arguments
#
if (len(sys.argv) == 1):
    timeStamp("ERROR. Please specify list of target names to process.")
    sys.exit()

#
# Grab the first (and hopefully only) argument as a file name.
#

fileName = sys.argv[1]

#
# This unfucks windows paths if relevant
#
newPathName = flipPath(fileName)

print("Processing: " + newPathName)

#
# Set some defaults for my camera that other people may not want.
#
if str(TSXSend('ccdsoftCamera.PropStr("m_csObserver")')) ==  "Ken Sturrock":
    if str(TSXSend("SelectedHardware.cameraModel")) == "QSI Camera  ":
        writeNote("Setting up Ken's QSI camera defaults.")
        TSXSend("ccdsoftCamera.TemperatureSetPoint = -10")
        TSXSend("ccdsoftCamera.RegulateTemperature = true")
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = 0")
        TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Faster Image Downloads")')

#
# Create variable to hold the star names
#
with open(newPathName) as starNameFile:
    starList = starNameFile.readlines()

# 
# Convert the string of names into a list
#
starList = [line.rstrip() for line in starList]


#
# Create a unique set.
#
for star in starList:
    if ("Object" not in star):
        uniqueTargSet.add(star)

#
# This re-sorts the set back to the optimized order that the SkyX creates.
uniqueTargSet = sorted(uniqueTargSet, key=starList.index)

#
# Convert the set back to a list
#
starList = list(uniqueTargSet)

#
# Remove extra spaces in the name from SkyX
#
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
    #
    # Is the target valid?
    #

        if (focusStyle == 2) or (focusStyle == 3):
        #
        # Do we have a focus method defined?
        #
            if (index % focusAfter == 0) or (initialFocused == "No"):
            #
            # This calls an initial focus and then one every defined number of stars.
            # The yes/no variable is only because if the first star is
            # invalid then it won't do the initial focus.
            #
                writeNote("Attempting to focus.")
                # This is a little redundant, but I slew to the star before focus because 
                # if the OTA has mirror slop, I want it to find focus in that part of the sky.
                slew(star)

                result = dsFocus(star)
                
                if result != "Success":
                    print("Focus failed!")
                    softPark()
                initialFocused = "Yes"
    
        # This will do the usual aiming & image steps.
        imageStar(star)

softPark()
