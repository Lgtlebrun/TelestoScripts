#!/usr/bin/env python3
#
# Run an automated session on SkyX.
#
# In addition to activating the TCP Server, you also have to switch on "TCP socket closing"
# under SkyX's Preferences -> Advanced.
#
# Syntax and functions are almost the same as the older Bash-based run_target script.
#
#       ./run_target-2 m51 5x300 5x300 5x300 5x300
#
# Second camera is activated with the "-r" option followed by the IP address and port
# of the second SkyX instance:
#
#       ./run_target-2 m51 5x300 5x300 5x300 5x300 -r 10.0.1.11:3040 3x240 3x240 3x240 3x240
#
# You can also add extra non-dithered frames to each set with an addition "x". For example:
#
#       ./run_target-2 m51 5x300x2 5x300 5x300 5x300
#
# will cause an LLRGB LLRGB pattern.
#
# Set the seven variables below. If you want to use @F3 instead of @F2, just change 
# the "focusStyle" variable below so that it reads ""Three" instead of "Two". 
# CaPiToLiZaTiOn matters, as do the quotes around Two and Three.
#
# Ken Sturrock
# March 24, 2023 
#

#############################
# User Modifiable Variables #
#############################



# How low can we start (in degrees)?
altLimit = 30

# Which filter number should we use for focuses and CLS? Probably luminance. Use quotes.
defaultFilter = "0"

# Do you use a default guider delay? Use quotes.
guiderDelay = "0"

# Set guiderExposure to 0 (zero) for guiderless or don't choose a guide camera in SkyX.
# Use quotes.
guiderExposure = "5"

# Which version of @Focus do you use? Two or Three? You can also say Zero for no auto-focus. 
# Use quotes and capitolization.
focusStyle = "Two"

# What amount of Celsius degree change will trigger a refocus.
tempChangeLimit = 0.5

# This is the hour angle at which the mount flips if a GoTo is commanded.
# Logically, a flip angle of zero is easiest to wrap your mind around but it
# can be anything so long as it matches what the mount does. If you are using
# a Paramount, consult your flip angle settings within Bisque TCS.
flipAngle = 0

# This is the settle time used by the program when shooting *unguided*. It is set by default 
# to 5 seconds with the ASSumption that anyone who shoots unguided is either using a Paramount 
# (or other high end mount) which doesn't require much settle time or has low standards.
# Note that no quotes are in use.
unGuidedSettle = 5



####################
# Import Libraries #
####################

from library.PySkyX_ks import *

import time
import sys
import os
import datetime

########################
# Script set Variables #
########################

filterNumC1 = 0
filterNumC2 = 0
perFilC1 = []
perFilC2 = []
numExpC1 = []
numExpC2 = []
expDurC1 = []
expDurC2 = []
totalExpC1 = 0
totalExpC2 = 0
numDupC1 = []
numDupC2 = []
dupGoalC1 = 1
dupGoalC2 = 1
expCountC1 = 1
expCountC2 = 1
totalSecC1 = 0
totalSecC2 = 0
numSets = 0
numSets1 = 0
numSets2 = 0
lastDitherImageC1 = 1
lastDitherImageC2 = 2


####################
# Define Functions #
####################



def chkTarget():
#
# This validates the target and ensures that it is up & that it's night.
#
    timeStamp("Target is " + target + ".")

    if targExists(target) == "No":
        writeError("" + target + " not found in SkyX database.")
        softPark()
    
    isDayLight()

    currentHA = targHA(target)
    currentAlt = targAlt(target) 

    if currentAlt < altLimit and currentHA > 0:
        timeStamp("Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
        timeStamp("Target " + target + " has sunk too low.")
        softPark()


    if currentAlt < altLimit and currentHA < 0:
    # This time mish-mash looks more elegant than just checking every five minutes but it's not.
    #
        targTimes = targRiseSetTimes(target, altLimit)
        riseTime = targTimes[0]
        riseHours,riseMinutes = riseTime.split(":")
        
        nowHours,nowMinutes = time.strftime("%H:%M").split(":")
        nowDec = HMSToDec(nowHours, nowMinutes, 0)
        nowDec = nowDec[3]
    
        riseDec = HMSToDec(riseHours, riseMinutes, 0)
        riseDec = riseDec[3]
    
        waitDec = riseDec - nowDec
        waitSec = int((waitDec * 3600) + 60)
    
        timeStamp("Waiting " + str(round(waitDec,2)) + " hours for target to rise.")
    
        time.sleep(waitSec)

        timeStamp("Checking target altitude.")

        # This code *should* no longer be necessary but serves as a double check in case I counted wrong.
        #
        currentAlt = targAlt(target) 
    
        while currentAlt < altLimit:
            writeNote("Target " + target + " is " + str(round(currentAlt, 2)) + " degrees high.")
            writeNote("Starting altitude is set for: " + str(altLimit) + " degrees.")
            writeNote("Target " + target + " is still too low.")
            timeStamp("Waiting five minutes.")
            time.sleep (300)
            currentAlt = targAlt(target) 


def doAnImage(exposureTime, FilterNum):
#
# This function performs the general steps required to take 
# an image. By default, it doesn't mess with the delay and
# only manipulates the camera. It does a follow-up on the
# tracking.
#

    global setLimit

    if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
        if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
            TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Higher Image Quality")')
            writeNote("Setting QSI Camera to high quality mode.")

    if takeImage("Imager", exposureTime, "NA", FilterNum) == "Success":

        if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":
            if TSXSend("SelectedHardware.cameraModel") == "QSI Camera  ":
                TSXSend('ccdsoftCamera.setPropStr("m_csExCameraMode", "Faster Image Downloads")')
                writeNote("Setting QSI Camera to faster download mode.")

        if guiderExposure != "0":
            if isGuiderLost(setLimit) == "Yes":
                #
                # If the guider looks lost, try it again
                #
                writeNote("Double Checking Guider.")
                time.sleep(5)
                if isGuiderLost(setLimit) == "Yes":
                    writeError("Guider looks lost")
                    return "Fail"
                else:
                    writeNote("Guiding is questionable.")
            else:
                writeNote("Guider Tracking.")
    
        if TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock":    
        #
        # If you're me....
        #
        # This bit of logic tries to determine if I'm running on a Raspberry Pi
        # and, if so, skip the statistics because it can take a long time
        # (like half a minute).
        #
        # This means that if I'm running unguided (unlikely) then there is
        # no cloud check.
        #
            OS = TSXSend("Application.operatingSystem")
            TSXSend('sky6RASCOMTele.DoCommand(15, "")')
            Platform = TSXSend("sky6RASCOMTele.DoCommandOutput")
          
            if (OS == "3") and (Platform == "arm"):
                writeNote("Raspberry Pi detected. Statistics skipped.")
            else:
                if getStats() == "Fail":
                    return "Fail"
        else:
            #
            # If you're not me, go ahead and run the statistics regardless
            # of platform because if I try to save you time then some 
            # compulsive person will whine about not getting the stats.
            #
            if getStats() == "Fail":
                return "Fail"


        if (TSXSend("ccdsoftCamera.ImageReduction") == "2"):
            Path = TSXSend("ccdsoftCameraImage.Path")
            dirName,fileName = os.path.split(Path)
            orgImgName = os.path.splitext(fileName)[0]            
            currentRGName = TSXSend('ccdsoftCamera.PropStr("m_csCalGroupName")')
            #
            # If the RG is the default "Imager" it's because we didn't really
            # calibrate it properly so let's lose the lie.
            #
            if currentRGName != "Imager":
            # Clean up the un-needed "uncalibrated" original images
                for scrapFile in glob.glob(dirName + "/" + "*Uncalibrated*.fit"):
                    if os.path.exists(scrapFile):
                        os.remove(scrapFile) 

                        # rename the calibrated image to indicate calibration
                        if os.path.exists(Path):
                            calPath = Path.replace(".fit", "_c.fit")
                            os.rename(Path, calPath)
            else:
            #
            # If we're using the default "Imager" RG then it probably isn't really
            # calibrated properly so we're going to clobber the calibrated
            # copy and rename the uncalibrated copy back without the "_c" suffix.
            #
                uncalPath = Path.replace(".fit", "Uncalibrated.fit")
                # Double check to make sure both files really exist.
                if os.path.exists(Path):
                    if os.path.exists(uncalPath):
                        os.remove(Path)
                        os.rename(uncalPath, Path)

        return "Success"

    else:
        return "Fail"

def focusAndDither(forceFocus, doDither):
#
# This routine runs the appropriate focus on both cameras (if applicable)
#
# Remember that this can get a bit mind-bending: This focus routine calls
# other focus routines in the library which may, in turn, call another focusing 
# routine. This whole thing is handled a bit inconsistantly with @F3 on two 
# cameras. Get your aspirin.
#
# The forceFocus flag forces a focus or leaves it up to the temperature & timing logic.
# The doDither flag forces a dither ("Yes") independent of focus. "No" prohibits
# a dither (for example an initial focus) and "Maybe" will dither only if the temp & time
# logic decides to focus.
#
# Parameters must be CaPiToLiZeD
#

    # This is a kludge, but I'm too lazy to pass them.
    global lastTemp
    global lastSeconds
    global lastDitherImageC1
    global lastDitherImageC2

    # This is a check to keep it from over dithering.
    # If the last dither was one filter ago on either camera, skip this dither
    # unless there's also a focus.
    #
    # The rig may still dither unnecessarily, for example if the target crosses the meridian
    # during a focus, but that's a very limited case.
    if doDither == "Yes":
        if ((expCountC1 - lastDitherImageC1) < 2):

            if (dupCounter < dupGoalC1):
                doDither = "Maybe"
            else:
                doDither = "Yes"

        elif camTwoIP != "none":
            if ((expCountC2 - lastDitherImageC2) < 2):
                doDither = "Maybe"
            else:
                doDither = "Yes"

        else:
            doDither = "Yes"


    currentTemp = getTemp()
    currentSeconds = round(time.monotonic(),0)

    if focusStyle != "Zero":
        # Is the temperature, elapsed time or a flag going to force us to focus? 
        # Note that this is set to refocus every half degree of change (or 45 minutes) because my SVQ seems to need it. Please
        # change the temperature limit (variable above) or the time (in seconds) below if you see the need.
        if (abs(lastTemp - currentTemp) > tempChangeLimit ) or ((currentSeconds - lastSeconds) > 2700) or (forceFocus == "Yes"):

            print("           -----")
            writeNote("Current Temperature: " + str(currentTemp))

            if guiderExposure != "0":
                stopGuiding()
                
            if camTwoIP == "none":
                if focusStyle == "Two":
                    if atFocus2(target, defaultFilter) != "Fail":
                        lastTemp = getTemp()
                        lastSeconds = round(time.monotonic(),0)
                else:
                    if atFocus3(target, defaultFilter) != "Fail":
                        lastTemp = getTemp()
                        lastSeconds = round(time.monotonic(),0)

                if (doDither == "Maybe"):
                    doDither = "Yes"

            else:
                if focusStyle == "Two":
                    if atFocus2Both(camTwoIP, target, defaultFilter) != "Fail":
                        lastTemp = getTemp()
                        lastSeconds = round(time.monotonic(),0)
                else:
                    if atFocus3(target, defaultFilter) != "Fail":
                        lastTemp = getTemp()
                        lastSeconds = round(time.monotonic(),0)
            
                        atFocusRemote(camTwoIP, "Imager", "Three", defaultFilter)

                if (doDither == "Maybe"):
                    doDither = "Yes"

    # So, in the end, did we decide to dither?                  
    if (doDither == "Yes"):
        print("           -----")
        if guiderExposure != "0":
            stopGuiding()
            
        dither()
        lastDitherImageC1 = expCountC1
        lastDitherImageC2 = expCountC2

    # These things shouldn't happen but let's look both ways on a one-way street.
    #
    # Did the mount flip unexpectedly (or not)? If so, realign on the target, dither be damned.
    # Strange stuff may happen here if you are not using a GEM.
    if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
        TSXSend('sky6RASCOMTele.DoCommand(11, "")')
        if (TSXSend("sky6RASCOMTele.DoCommandOutput") == "1") and (targHA(target) > flipAngle):
            writeError("The target is west of the meridian but the mount has not appeared to flip.")
            writeNote("Using CLS to ensure target alignment.")
            if CLSlew(target, defaultFilter) == "Fail":
                timeStamp("Error finding target post-flip. Stopping script.")
                hardPark()
            
                    
        if (TSXSend("sky6RASCOMTele.DoCommandOutput") == "0") and (targHA(target) <= flipAngle):
            writeError("The target is still east of the meridian but the mount appears to have flipped.")
            writeNote("Using CLS to ensure target alignment.")
            if CLSlew(target, defaultFilter) == "Fail":
                timeStamp("Error finding target post-flip. Stopping script.")
                hardPark()

            lastTargHA = targHA(target)

    # if we're not guiding and should, restart it.
    # otherwise, settle with a wait if we dithered.
    if (guiderExposure != "0"):
        if (TSXSend("ccdsoftAutoguider.State") != "5"):
            stopGuiding()
            setupGuiding()

    elif (doDither == "Yes"):
        timeStamp("Waiting for mount to settle.")
        time.sleep(unGuidedSettle)
       

def houseKeeping():
#
# This covers functions that used to occur between sets but
# are now handled between images.
#
    global lastTargHA


    # Just in case, because sometimes weird counting happens
    if (expCountC2 > totalExpC2) and (expCountC1 > totalExpC1):
        hardPark()

    # If it is morning, shut it down.
    if setCounter <= numSets:
        isDayLight()
    
    # If the target is low, shut it down.    
    if targAlt(target) < 35 and targHA(target) > 0:
        timeStamp("Target has sunk too low.")
        hardPark()
    
    # If the target crossed the meridian, flip the mount.
    if targHA(target) > flipAngle and lastTargHA <= flipAngle:
        timeStamp("Target has crossed the meridian.")

        if guiderExposure != "0":
            stopGuiding()
            writeNote("Guiding Stopped.")

        if CLSlew(target, defaultFilter) == "Fail":
            timeStamp("Error finding target post-flip. Stopping script.")
            hardPark()
            
        #
        # This forces a focus after a meridian flip in case something mechanical moved.
        #
        # There is no reason to dither since you just changed the FOV by flipping
        #
        focusAndDither("Yes", "No")

        # Go ahead and reset the last dither filters though because we did the
        # equivelent of a dither by flipping the mount.
        lastDitherImageC1 = expCountC1
        lastDitherImageC2 = expCountC2

    else:
        if (fCounter < (totalFilC1 - 1)) or (fCounter < (totalFilC2 - 1)):
        #
        # If this is not the last filter in the set, offer a refocus if needed.
        # 
        # Dither only if there was a refocus. Otherwise, keep on truckin'

            focusAndDither("No", "Maybe")

        else:
        # This should get called after the last filter in the set (logic below should
        # prevent being called after final image)
        # It allows a focus and requests a dither.
            if setCounter < numSets:
                focusAndDither("No", "Yes")

    lastTargHA = targHA(target)

def setupGuiding():
#
# This is a "macro" that calls several simpler functions in 
# order to setup autoguiding.
#

    global setLimit

    camConnect("Guider")

    stopGuiding()

    time.sleep(1)

    # Take an image of the guider FOV
    takeImage("Guider", guiderExposure, "0", "NA")

    # Pick a decent guide star.
    AGStar = findAGStar()

    if "Error" in AGStar:
    # Not off to a good start....

        cloudWait(defaultFilter)

        if CLSlew(target, defaultFilter) == "Fail":
            timeStamp("There was an error CLSing to Target. Stopping script.")
            hardPark()

        lastTargHA = targHA(target)
        
        takeImage("Guider", guiderExposure, "0", "NA")

        AGStar = findAGStar()
     
        if "Error" in AGStar:
            writeError("Still cannot find a guide star. Sorry it didn't work out...")
            hardPark()
        else:
            XCoord,YCoord = AGStar.split(",")
    else:    
    # Split the coordinates into separate variables.
        XCoord,YCoord = AGStar.split(",")

    # Do the math to calculate a "good enough" guider error limit.
    setLimit = calcSettleLimit()

    # Do we need to adjust the guider exposure? In theory, the star should not
    # be saturated, but this will also boost the guider exposure time if the 
    # guide star is dim.
    expRecommends = adjAGExposure(guiderExposure, guiderDelay, XCoord, YCoord)
    newGuiderExposure = expRecommends[0]
    newGuiderDelay = expRecommends[1]

    # Start guiding
    startGuiding(newGuiderExposure, newGuiderDelay, XCoord, YCoord)

    # Wait until the guider/mount is settled or lost. If it gets
    # lost then retry it.
    if settleGuider(setLimit) == "Lost":
        writeError("Guiding setup failed.")
        stopGuiding()
                
        cloudWait(defaultFilter)
                
        if CLSlew(target, defaultFilter) == "Fail":
            timeStamp("There was an error CLSing to Target. Stopping script.")
            hardPark()
                
        lastTargHA = targHA(target)
        
        takeImage("Guider", guiderExposure, "0", "NA")

        AGStar = findAGStar()

        if "Error" in AGStar:
            writeError("Still have problems setting up guider. Exiting.")
            softPark()

        XCoord,YCoord = AGStar.split(",")

        startGuiding(guiderExposure, guiderDelay, XCoord, YCoord)

        if settleGuider(setLimit) == "Lost":
            writeError("Guiding setup failed again.")
            hardPark()



       
######################
# Main Program Start #
######################

timeStamp("Run started")

print("     DATE: " + datetime.date.today().strftime("%Y" + "-" + "%B" + "-" + "%d"))

tcpChk()

writeNote("SkyX Pro Build Level: " + TSXSend("Application.build"))

if sys.platform == "win32":
    writeNote("Running on Windows.")

if sys.platform == "darwin":
    writeNote("Running on Macintosh.")

if sys.platform == "linux":
	if os.uname()[4].startswith("arm"):
		writeNote("Running on R-Pi.")
	else:
		writeNote("Running on Linux.")

#
# preRun checks some settings to head off questions later
#
if preRun() == "Fail":
    sys.exit()

# Turn off guiding functions if no guider chosen in SkyX.
if TSXSend("SelectedHardware.autoguiderCameraModel") == "<No Camera Selected>":
    guiderExposure = "0"

if guiderExposure == "0":
    writeNote("Guiding disabled.")

if TSXSend("SelectedHardware.focuserModel") ==  "<No Focuser Selected>":
    focusStyle = "Zero"

if focusStyle == "Zero":
    writeNote("Autofocus disabled.")

# For those so blessed
domeStart()


#####################################################################
# Take apart the arguments to figure out what the user wants to do. #
#####################################################################

totalArgs = (len(sys.argv) - 2)

if totalArgs < 1:
#
# If the user hasn't specified command line arguments, fire up the GUI.
#
    timeStamp("Incomplete command line arguments.")
    print("           Syntax: " + sys.argv[0] + " target FxE FxE ...")
    
    print(" ")
    print("----------")
    timeStamp("Launching graphical interface.")

    # Only load the GUI libraries if they need to be used.
    from library.RT_GUI import runGUI
    
    GUIresults = runGUI()
    timeStamp("Closing graphical interface.")
    print("----------")
    print(" ")

    argumentArray = GUIresults[0]
    guiderExposure = GUIresults[1]
    guiderDelay = GUIresults[2]
    focusStyle = GUIresults[3]

else:
    argumentArray = sys.argv

totalArgs = (len(argumentArray) - 2)

target = argumentArray[1]

camOneExp = []
camTwoExp = []
camTwoIP = "none"

counter = 1

while counter <= totalArgs:
    if argumentArray[counter + 1] == "-r":
        if (counter) < totalArgs:
            if "." in argumentArray[counter + 2]:
                camTwoIP = argumentArray[counter + 2]
                counter = counter + 2
            else:
                print("Invalid or incomplete IP address specified for second camera.")
                sys.exit()
        else:
            print("Insufficient arguments provided to specify second camera.")
            sys.exit()

        while counter <= totalArgs:
            camTwoExp.append(argumentArray[counter + 1])
            counter = counter + 1

    else:
        camOneExp.append(argumentArray[counter + 1])

    counter = counter + 1

totalFilC1 = len(camOneExp)
totalFilC2 = len(camTwoExp)

if totalFilC1 > totalFilC2:
    totalFil = totalFilC1
else:
    totalFil = totalFilC2

########################
# Is the target valid? #
########################

chkTarget()

writeNote("Checking cameras.")
camConnect("Imager")

if camTwoIP != "none":
    camConnectRemote(camTwoIP, "Imager")

if str(TSXSend("SelectedHardware.mountModel")) ==  "Telescope Mount Simulator":
    writeNote("Simulated Mount.")
else:
    writeNote("Checking sidereal drive.")
    TSXSend("sky6RASCOMTele.SetTracking(1, 1, 0 ,0)")

if camTwoIP != "none":
    writeNote("Remote SkyX Pro Build Level: " + TSXSendRemote(camTwoIP, "Application.build"))

    OS = TSXSendRemote(camTwoIP, "Application.operatingSystem")
    TSXSendRemote(camTwoIP,'sky6RASCOMTele.DoCommand(15, "")')
    Platform = TSXSendRemote(camTwoIP,"sky6RASCOMTele.DoCommandOutput")
          
    if (OS == "1"):
        writeNote("Remote system running on Windows")

    if (OS == "2"):
        writeNote("Remote system running on Macintosh")
                

    if (OS == "3"):
        if (Platform == "arm"):
            writeNote("Remote system running on R-Pi")
        elif (Platform == "arm64"):
            writeNote("Remote system running on Linux (ARM64)")
        else:
            writeNote("Remote system running on Linux")


#############################################
# Work out the imaging plan and explain it. #
#############################################

print("     PLAN:")

print("           Local Camera")
print("           ------------")

while filterNumC1 < totalFilC1:
    
    perFilC1.append(camOneExp[filterNumC1])


    if perFilC1[filterNumC1].count("x") == 1:
        num,dur=perFilC1[filterNumC1].split("x")
        dup=1

    if perFilC1[filterNumC1].count("x") == 2:
        num,dur,dup=perFilC1[filterNumC1].split("x")

    numDupC1.append(int(dup))
    numExpC1.append(int(num))
    expDurC1.append(int(dur))

    if numDupC1[filterNumC1] == 1:
        adjExposureNum = numExpC1[filterNumC1]
    else:
        adjExposureNum = (numExpC1[filterNumC1] * numDupC1[filterNumC1])

    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        filName = TSXSend("ccdsoftCamera.szFilterName(" + str(filterNumC1) + ")")
    else:
        filName = "no"
     
    print ("           " + str(adjExposureNum) + " exposures for " + str(expDurC1[filterNumC1]) + " secs. with " + filName + " filter.")
    
    totalExpC1 = totalExpC1 + adjExposureNum
    totalSecC1 = totalSecC1 + (expDurC1[filterNumC1] * adjExposureNum)

    if numExpC1[filterNumC1] > numSets1:
        numSets1 = numExpC1[filterNumC1]
    
    filterNumC1 = filterNumC1 + 1
    
print("           -----")
print("           " + str(totalExpC1) + " total exposures for " + str(round((totalSecC1 / 60), 2)) + " total minutes.")
print("           -----")


if camTwoIP != "none":

    print(" ")
    print("           Remote Camera")
    print("           -------------")

    while filterNumC2 < totalFilC2:

        perFilC2.append(camTwoExp[filterNumC2])

        if perFilC2[filterNumC2].count("x") == 1:
            num,dur=perFilC2[filterNumC2].split("x")
            dup=1

        if perFilC2[filterNumC2].count("x") == 2:
            num,dur,dup=perFilC2[filterNumC2].split("x")
    
        numDupC2.append(int(dup))
        numExpC2.append(int(num))
        expDurC2.append(int(dur))
    
        if numDupC2[filterNumC2] == 1:
            adjExposureNum = numExpC2[filterNumC2]
        else:
            adjExposureNum = (numExpC2[filterNumC2] * numDupC2[filterNumC2])

        if TSXSendRemote(camTwoIP,"SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
            filName = TSXSendRemote(camTwoIP,"ccdsoftCamera.szFilterName(" + str(filterNumC2) + ")")
        else:
            filName = "no"

        print ("           " + str(adjExposureNum) + " exposures for " + str(expDurC2[filterNumC2]) + " secs. with " + filName + " filter.")
        
        totalExpC2 = totalExpC2 + adjExposureNum
        totalSecC2 = totalSecC2 + (expDurC2[filterNumC2] * adjExposureNum)

        if numExpC2[filterNumC2] > numSets1:
            numSets1 = numExpC2[filterNumC2]
    
        filterNumC2 = filterNumC2 + 1
    
    print("           -----")
    print("           " + str(totalExpC2) + " total exposures for " + str(round((totalSecC2 / 60), 2)) + " total minutes.")
    print("           -----")
    print(" ")

if numSets1 >= numSets2:
    numSets = numSets1
else:
    numSets = numSets2

######################################
# Move the mount and start the setup #
######################################

# I do this because, with @F2 and a Paramount, the initial CLS is wasted
if (TSXSend('ccdsoftCamera.PropStr("m_csObserver")') == "Ken Sturrock") and \
        ("Paramount" in TSXSend("SelectedHardware.mountModel")) and \
        (focusStyle == "Two"):
        slew(target)

# Same with the simulator.
elif TSXSend("SelectedHardware.mountModel") ==  "Telescope Mount Simulator":
    slew(target)

else:
    if CLSlew(target, defaultFilter) == "Fail":
        timeStamp("There was an error on initial CLS. Stopping script.")
        softPark()


if camTwoIP != "none":
    slewRemote(camTwoIP, target)


# These are used in the refocus logic and need to be seeded.
lastTemp = getTemp()
lastSeconds = 0

# This is used in the flip-logic and needs to be seeded.
lastTargHA = targHA(target)

# Run an initial focus but don't dither.
#
# Guiding has to be set up independently because the focus
# routine only sets up guiding if a dither occured.

if focusStyle == "Zero":
    # If there is no focuser but we are guiding, setup guiding
    if guiderExposure != "0":
        setupGuiding()
        
    # if there is no focuser and no guiding, wait 20 seconds to settle
    else:
        timeStamp("Waiting for mount to settle.")
        time.sleep(unGuidedSettle)

# if there is a focuser but no guider then wait as a settle
elif guiderExposure == "0":
    timeStamp("Waiting for mount to settle.")
    time.sleep(unGuidedSettle)

# if there is a focuser and a guider then focus & setup guiding.
else:
    focusAndDither("Yes", "No")


###############################
# Start the main imaging loop #
###############################

setCounter = 1 

while setCounter <= numSets:

    fCounter = 0

    while fCounter < totalFil:

        dupCounter = 1
        dupGoalC1 = 1
        dupGoalC2 = 1
       
        if (fCounter <= len(numDupC1) - 1):
            dupGoalC1 = numDupC1[fCounter]

        if (fCounter <= len(numDupC2) - 1):
            dupGoalC2 = numDupC2[fCounter]

        while (dupCounter <= dupGoalC1) or (dupCounter <= dupGoalC2):

            if (fCounter <= (totalFilC2 - 1)) and (numExpC2[fCounter] > 0) and (dupCounter <= dupGoalC2):

                print("           -----")
                writeNote("Starting remote camera image " + str(expCountC2) + " of " + str(totalExpC2) + ".")
                
                takeImageRemote(camTwoIP, "Imager", str(expDurC2[fCounter]), "0", str(fCounter))
   
            if (fCounter <= (totalFilC1 - 1)) and (numExpC1[fCounter] > 0) and (dupCounter <= dupGoalC1):
                print("           -----")
                writeNote("Starting local camera image " + str(expCountC1) + " of " + str(totalExpC1) + ".")
                expCountC1 = expCountC1 + 1
    
                if doAnImage(str(expDurC1[fCounter]), str(fCounter)) == "Fail":
                    
                    # What if things go wrong?
                    writeError("Camera problem or clouds..")

                    if guiderExposure != "0":
                        stopGuiding()
    
                    cloudWait(defaultFilter)

                    if CLSlew(target, defaultFilter) == "Fail":
                        timeStamp("There was an error CLSing to Target. Stopping script.")
                        hardPark()
    
                    lastTargHA = targHA(target)

                    #
                    # If we are guiding then re-start guiding
                    # this is similar but slightly different than the
                    # function above because we don't want a retry in case
                    # of failure
                    #
                    if guiderExposure != "0":

                        takeImage("Guider", guiderExposure, "0", "NA")

                        AGStar = findAGStar()

                        if "Error" in AGStar:
                            writeError("Still have problems setting up guider. Exiting.")
                            softPark()

                        XCoord,YCoord = AGStar.split(",")

                        setLimit = calcSettleLimit()

                        startGuiding(guiderExposure, guiderDelay, XCoord, YCoord)
  
                        if settleGuider(setLimit) == "Lost":
                            writeError("Unable to setup guiding.")
                            hardPark()
                        else:
                            writeNote("Attempting to retake image.")
                            if doAnImage(str(expDurC1[fCounter]), str(fCounter)) == "Fail":
                                writeError("There is still a problem.")
                                hardPark()
                            else:
                                writeNote("Resuming Sequence.")

                    ##########################

            if (fCounter <= (totalFilC2 - 1)) and (numExpC2[fCounter] > 0) and (dupCounter <= dupGoalC2):
                remoteImageDone(camTwoIP, "Imager")
                getStatsRemote(camTwoIP, "Imager")
                expCountC2 = expCountC2 + 1


            houseKeeping()


            dupCounter = dupCounter + 1

        if (fCounter <= (totalFilC1 - 1)) and (numExpC1[fCounter] > 0):
            numExpC1[fCounter] = numExpC1[fCounter] - 1

        if (fCounter <= (totalFilC2 - 1)) and (numExpC2[fCounter] > 0):
            numExpC2[fCounter] = numExpC2[fCounter] - 1

        fCounter = fCounter + 1

    setCounter = setCounter + 1

writeGap()

# The regular park doesn't shutdown the remote camera.
if camTwoIP != "none":
    writeNote("Disconnecting remote camera.")
    camDisconnectRemote(camTwoIP, "Imager")

hardPark()

