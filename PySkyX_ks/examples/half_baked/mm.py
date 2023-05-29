#!/usr/bin/env python3
#
# Tries to estimate the magnitude of the image's target based upon a regression
# of other stars in the image.
#
# Ken Sturrock
# June 26, 2021
#

from library.PySkyX_ks import *

import sys
import os
import math
import statistics
import time

def qClassicIL():
#
# Another quiet version of the one found in PySkyX_ks
#

    FITSProblem = "No"

    if "undefined" in str(TSXSend('ccdsoftCameraImage.FITSKeyword("FOCALLEN")')):
        writeError("Bogus File")
        return "Fail"

    if TSXSend("ccdsoftCameraImage.ImageUseDigitizedSkySurvey") == "1":
        FITSProblem = "Yes"
        
    else:
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

    # get the determined IS and use it in place of our earlier guess.
    newIS = TSXSend("ImageLinkResults.imageScale")

    TSXSend("ImageLink.scale = " + str(newIS))

    # Now that we, hopefully, know the image link, we'll turn off the unknown IS option for anything
    # downstream. Much of the current code, will ignore this and re-guess it for later.  
    TSXSend("ImageLink.unknownScale = 0")

    TSXSend("ccdsoftCameraImage.ScaleInArcsecondsPerPixel = " + str(newIS))         

    return ilResults



def closeImage():
#
# Closes the active image
#
    TSXSend("ccdsoftCameraImage.Close()")


def openImage(imgPath):
#
# This will open up the image in question and run Image Link.
# It will leave the image open for subsequent analysis.
#

    imgPath = flipPath(imgPath)

    TSXSend("ccdsoftCameraImage.DetachOnClose = 0")
    TSXSend('ImageLink.pathToFITS = "' + imgPath + '"')
    TSXSend('ccdsoftCameraImage.Path = "' + imgPath + '"')
    TSXSend("ccdsoftCameraImage.Open()")

    ilResults = qClassicIL()

    if ("rror:" in ilResults) or ("Fail" in ilResults):
        writeError("Image Link Failed.")
        writeError("" + ilResults)

        TSXSend("ccdsoftCameraImage.Close()")
        TSXSend('ImageLink.pathToFITS = " "')

        return "Fail"

    else:
        timeStamp("Image Link Successful.")

    TSXSend("ccdsoftCameraImage.InsertWCS()")

    lsNum = TSXSend("ccdsoftCameraImage.InventoryArray(0).length")

    lsXRaw = TSXSend("ccdsoftCameraImage.InventoryArray(0)")
    lsYRaw = TSXSend("ccdsoftCameraImage.InventoryArray(1)")
    lsMagRaw = TSXSend("ccdsoftCameraImage.InventoryArray(2)")
    targFWHMRaw = TSXSend("ccdsoftCameraImage.InventoryArray(4)")
    ilFWHM = float(TSXSend("ImageLinkResults.imageFWHMInArcSeconds"))
            
    lsXArray = lsXRaw.split(",")
    lsYArray = lsYRaw.split(",")
    lsMagArray = lsMagRaw.split(",")
    targFWHMArray = targFWHMRaw.split(",")

    TSXSend('sky6StarChart.Find("Z 0.5")')
    TSXSend("sky6StarChart.Refresh()")
 
    return [lsXArray, lsYArray, lsMagArray, targFWHMArray, ilFWHM]

def qLinReg(arrayX, arrayY):
#
# This is a less verbose (quiet) version of the linear regression routine from PySkyX_ks
#
    sum_x = 0
    sum_y = 0
    sum_xy = 0
    sum_xx = 0
    sum_yy = 0
    slope = 0
    intercept = 0
    r2 = 0
    n = len(arrayX)

    for counter,Xvalue in enumerate(arrayX):
        Yvalue = arrayY[counter]
        sum_x = sum_x + Xvalue;
        sum_y = sum_y + arrayY[counter];
        sum_xy = sum_xy + (Xvalue * Yvalue)
        sum_xx = sum_xx + (Xvalue * Xvalue)
        sum_yy = sum_yy + (Yvalue * Yvalue)

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)

    intercept = (sum_y - slope * sum_x) / n

    term1 = (n * sum_xy - sum_x * sum_y)
    term2 = (n * sum_xx - sum_x * sum_x)
    term3 = (n * sum_yy - sum_y*sum_y)
    term4 = term2 * term3
    term4 = abs(term4)
    term5 = math.sqrt(term4)

    r2 = math.pow((term1 / term5),2)
  
    return [float(intercept), float(slope), float(r2)]


def XYToRADec(targX, targY):
#
# I have a nicer stand-alone version of this in the library, but for our 
# purposes, this is a lot faster.
#
    TSXSend("ccdsoftCameraImage.XYToRADec(" + str(targX) + ", " + str(targY) + ")")
    RAj2k = TSXSend("ccdsoftCameraImage.XYToRADecResultRA()")
    DecJ2k = TSXSend("ccdsoftCameraImage.XYToRADecResultDec()")
 
    return [RAj2k, DecJ2k]


def getTargCoords(target):
#
# This returns the X, Y & RA, Dec coordinates based on a target search string.
# There is extra complexity because it doesn't just blindly translate, it
# goes back and snaps to the LS in the image for a more precise X,Y centroid.
#

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


def AAadu(targX, targY, targFWHM):
#
# A slightly more refined average ADU measurement routine based on an apperture & annulus.
#

    targX = int(round(float(targX),0))
    targY = int(round(float(targY),0))
    origTargFWHM = targFWHM
    targFWHM = math.ceil(float(targFWHM))


    def ringCoords(pointX, pointY, R):
    #
    # Take the X, Y and Radius of a star centroid and figure out reasonable aperture and annulus circles.
    # Return the X,Y values of points within the circle and ring as four arrays.
    #
    
        def isXYinCircle(X, Y, R):
        #
        # X and Y are coordinates of pixel and r is radius of circle.
        # Tell us if the specific point is in the circle
        #
            if ((X*X) + (Y*Y) <= (R*R)):
                return True
    
        # Take the parameters, regardless of type and turn them into rounded integers
        pointX = int(round(float(pointX),0))
        pointY = int(round(float(pointY),0))
        # change the value multiplied by R to scale the aperture
        R = int(round(float(R * 0.8),0))
    
        apertureX = []
        apertureY = []
        annulusX = []
        annulusY = []
    
        boxSize = 4
    
        startX = int(pointX - (boxSize * R))
        endX = int(pointX + (boxSize * R))
    
        while (startX <= endX):
    
            startY = int(pointY - (boxSize * R))
            endY = int(pointY + (boxSize * R))
    
            while (startY <= endY):   
                relativeX = abs(startX - pointX)
                relativeY = abs(startY - pointY)
    
                result = isXYinCircle(relativeX, relativeY, R)
    
                if (result == True):
                    apertureX.append(startX)
                    apertureY.append(startY)
    
                else:
    
                    # adjust these values to change the outer edge of the gap and annulus
                    #
                    isGap = isXYinCircle(relativeX, relativeY, (R + (0.5 * R)))
                    isAnnulus = isXYinCircle(relativeX, relativeY, (R + (1.0 * R)))
                        
                    if (isAnnulus == True) and (isGap != True):
                        annulusX.append(startX)
                        annulusY.append(startY)
    
                startY = startY + 1
    
            startX = startX + 1
    
        return [apertureX, apertureY, annulusX, annulusY]

    def apAn(apXarray, apYarray, anXarray, anYarray):
    # 
    # Does the actual calculation of the average ADU by calculating it
    # for the coordinates that fall within the Annulus & Aperture and then
    # calculating the difference.
    #
    # I used to also calculate the median but found during tests that, surprisingly,
    # it was less stable than the mean.
    #
                    
        apAduXY = []
        anAduXY = []

        if len(anXarray) < 1:
            return "Fail"

        for Y in apYarray:
            lineValuesArray = []
            lineValuesArray = TSXSend("ccdsoftCameraImage.scanLine(" + str(Y) + ")").split(",")
    
            xLength = len(apXarray)
            index = 0
    
            while index < xLength:
                if apYarray[index] == Y:
                    apAduXY.append(int(lineValuesArray[apXarray[index]]))
                index = index + 1
    
        for Y in anYarray:
            lineValuesArray = []
            lineValuesArray = TSXSend("ccdsoftCameraImage.scanLine(" + str(Y) + ")").split(",")
    
            xLength = len(anXarray)
            index = 0
    
            while index < xLength:
                if anYarray[index] == Y:
                    anAduXY.append(int(lineValuesArray[anXarray[index]]))
                index = index + 1
    
        meanApADU = int(statistics.mean(apAduXY))
        meanAnADU = int(statistics.mean(anAduXY))
    
        meanADU = meanApADU - meanAnADU
    
        return meanADU
    

    imageWidth = int(TSXSend("ccdsoftCameraImage.WidthInPixels"))
    imageHeight = int(TSXSend("ccdsoftCameraImage.HeightInPixels"))

    safeYmin = targFWHM * 4
    safeYmax = imageHeight - (targFWHM * 4)
    safeXmin = targFWHM * 4
    safeXmax = imageWidth - (targFWHM * 4)

    if (targX < safeXmax) and (targX > safeXmin) and (targY < safeYmax) and (targY > safeYmin) and (targFWHM >= 1):
    #
    # Make sure that we're not rubbing too close against an edge source. Protect against bizarre negative FWHMs from
    # the Sex Tractor.
    #
    
        # Call the ringCoords routine to get the coordinates of the aperture and annulus pixels to sample for the light source.
        results = ringCoords(targX, targY, targFWHM)
    
        # The returned results are an array/list or arrays/lists representing the coordinates for the pixels that make up the 
        # aperture [0 & 1] and annulus [2 & 3]
    
        apX = results[0]
        apY = results[1]
        anX = results[2]
        anY = results[3]
    
        # Read the values for the pixels, do the averages and subtraction.
        meanADU = apAn(apX, apY, anX, anY)


        if meanADU == "Fail":
            closeImage()

            print("ERROR")

            print("X: " + str(targX))
            print("Y: " + str(targY))
            print("Orig. FWHM: " + str(origTargFWHM))
            print("New FWHM: " + str(targFWHM))

            print("SafeYmin: " + str(safeYmin))

            sys.exit()


        # This converts an average ADU value in arbitrary X bit space into a normalized 0 -> 1 value for brightness.
        imageDepth = TSXSend('ccdsoftCameraImage.FITSKeyword("BITPIX")')
        if "Error = 250" in imageDepth:
            writeError("FITS Keyword BITPIX not found. Assuming 16-bit.")
            imageDepth = 16
        else:
            imageDepth = int(imageDepth)
    
        fullWell = int(math.pow (2, imageDepth))
        brightness = round(((meanADU / fullWell) * 100), 3)
    
        return brightness

    else:
        return ""


def getGaiaAPASSmag(targRA, targDec, limit):
#
# This is a modification of the namesAt routine simplified
# and inclusive of an APASS call-out. 
#

    targRA = float(targRA)
    targDec = float(targDec)
    limit = float(limit) * 2
    target = str(targRA) + ", " + str(targDec)

    closestGaia = limit
    closestAPASS = limit
    gaiaMag = 9999
    APASSmag = -31.07
    normStar = "yes"
    
    TSXSend('sky6StarChart.Find("' + target + '")')

    TSXSend('sky6StarChart.EquatorialToStarChartXY(' + target + ')')
    
    targX = TSXSend("sky6StarChart.dOut0")
    targY = TSXSend("sky6StarChart.dOut1")

    TSXSend("sky6StarChart.ClickFind(" + targX + ", " + targY + ")")

    numObjects = int(TSXSend("sky6ObjectInformation.Count")) 

    for objectIndex in range(numObjects + 1):
        TSXSend("sky6ObjectInformation.Index = " + str(objectIndex))

        TSXSend("sky6ObjectInformation.Property(12)")		
        objType = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
        if objType == "Variable Star":
            writeNote("Variable Star detected.")
            normStar = "no"
            
        for nameIndex in range(8):
            TSXSend("sky6ObjectInformation.Property(" + str(nameIndex) + ")")
            objName = TSXSend("sky6ObjectInformation.ObjInfoPropOut")
            if ("Gaia" in objName):
                TSXSend("sky6ObjectInformation.Property(56)")
                objRAj2k = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 
                objRAj2k = str(float(objRAj2k))
    
                TSXSend("sky6ObjectInformation.Property(57)")
                objDecj2k = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 
                objDecj2k = str(float(objDecj2k))

                TSXSend("sky6Utils.ComputeAngularSeparation(" + target + ", " \
                    + objRAj2k + ", " + objDecj2k +")")

                distInAS = 3600 * float(TSXSend("sky6Utils.dOut0"))
                distInAS = round(distInAS,2)

                if distInAS < closestGaia:
                    closestGaia = distInAS
                    TSXSend("sky6ObjectInformation.Property(65)")
                    gaiaMag = round(float(TSXSend("sky6ObjectInformation.ObjInfoPropOut")),2)

            if ("APASS" in objName):
                TSXSend("sky6ObjectInformation.Property(56)")
                objRAj2k = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 
                objRAj2k = str(float(objRAj2k))

                TSXSend("sky6ObjectInformation.Property(57)")
                objDecj2k = TSXSend("sky6ObjectInformation.ObjInfoPropOut") 
                objDecj2k = str(float(objDecj2k))

                TSXSend("sky6Utils.ComputeAngularSeparation(" + target + ", " \
                    + objRAj2k + ", " + objDecj2k +")")

                distInAS = 3600 * float(TSXSend("sky6Utils.dOut0"))
                distInAS = round(distInAS,2)

                if distInAS < closestAPASS:
                    closestAPASS = distInAS
                    TSXSend("sky6ObjectInformation.Property(65)")
                    APASSmag = round(float(TSXSend("sky6ObjectInformation.ObjInfoPropOut")),2)

    return [normStar, gaiaMag, APASSmag]



###########################
# Start of actual program #
###########################

CR = "\n"

argvLen = len(sys.argv)

if (argvLen == 1):
    timeStamp("ERROR. Please specify image names to process.")
    sys.exit()
 
if sys.platform == "win32":
    fileList = []
    
    for fileName in glob.glob(sys.argv[1]):
        fileList.append(fileName)
else:
    fileList = sys.argv
    fileList.pop(0)

fileNum = len(fileList)
            
for count, imgPath in enumerate(fileList, start=1):

    print("--------------------------------------------------------------------------------")
    print("Processing: " + str(count) + " of " + str(fileNum))
    print("--------------------------------------------------------------------------------")

    magList = []
    SEmagList = []
    prettyRADecList = []
    obsDateList = []
    regGaiaMagList = []
    regAPASSmagList = []
    gaiaMagList = []
    APASSmagList = []
    SEmagList_Gaia = []
    SEmagList_APASS = []
    adjSEmagList_APASS = []
    adjSEmagList_Gaia = []


    results = openImage(imgPath)

    if results != "Fail":
    #    
    # Try to get the intended target name
    #
        targName = TSXSend('ccdsoftCameraImage.FITSKeyword("OBJECT")')

        # Clip out the ugly excess spaces that are probably in the target name.
        targName = " ".join(targName.split())

        # Get the X,Y & RA,Dec coordinates associated with this object.
        results2 = getTargCoords(targName)

    if (results == "Fail") or (results2 == "Fail"):
    #
    # Proceed only if we were able to BOTH open the file and extract a
    # set of target coordinates.
    #
        writeError("Image analysis failed.")
        closeImage()

    else:
        lsXArray = results[0]
        lsYArray = results[1]
        lsMagArray = results[2]
        targFWHMArray = results[3]
        numSources = len(lsXArray)
        imageScale = float(TSXSend("ImageLinkResults.imageScale"))

        targetLS = results2[4]

        timeStamp("Looking up catalog magnitudes.")
        writeGap()
    
        print("Number\t\tGaia\tAPASS\tRaw SE\tFWD%")
        print("------\t\t----\t-----\t------\t-------")

        midPointTime = getMidPointTime()


        for index in range(numSources):
   
            targX = float(lsXArray[index])
            targY = float(lsYArray[index])
    
            results = XYToRADec(lsXArray[index], lsYArray[index])
            targRA = results[0]
            targDec = results[1]

            targFWHM = float(targFWHMArray[index])
            targFWHMas = targFWHM * imageScale
            seMag = round(float(lsMagArray[index]), 2)
    
            results = getGaiaAPASSmag(targRA, targDec, targFWHMas)
            normStar = results[0]
            targGaiaMag = results[1]
            targAPASSmag = results[2]
    
            # Institute some clumsy missing data switches.
            if (targGaiaMag != 9999):
                targGaiaMag = float(targGaiaMag)
            else:
                targGaiaMag = ""
    
            if (targAPASSmag != 9999) and (targAPASSmag != -31.07):
                targAPASSmag = float(targAPASSmag)
            else:
                targAPASSmag = ""

            # This is the light source mean ADU experessed as a full well depth percent.
            
            FWDperc = AAadu(targX, targY, targFWHM)

            prettyCount = ("(" + str(index + 1) + " of " + str(numSources) + ")")
    
            print(str(prettyCount) + "\t" + str(targGaiaMag) + "\t" + str(targAPASSmag) + \
                    "\t" + str(seMag) + "\t" + str(FWDperc)) 

            gaiaMagList.append(targGaiaMag)
            APASSmagList.append(targAPASSmag)
            
            SEmagList.append(seMag)

            prettyRADec = (targRA + ", " + targDec).ljust(42, " ")
            prettyRADecList.append(prettyRADec)
        
            obsDateList.append(midPointTime)

            # Save aside the magnitudes for the target (may be blank)
            # if not the target, use the source for regression.
            if targetLS == index:
                realtargGaiaMag = targGaiaMag
                realtargAPASSmag = targAPASSmag
            else:
                # This creates value lists for Gaia & APASS-based regressions only if there is a legit value.
                if normStar == "yes":
                    if (targAPASSmag != ""):
                        regAPASSmagList.append(targAPASSmag)
                        SEmagList_APASS.append(seMag)
                
                    if (targGaiaMag != ""):
                        regGaiaMagList.append(targGaiaMag)
                        SEmagList_Gaia.append(seMag)


        closeImage()
    
        writeGap()
    
        if (len(SEmagList) > (index/2)):
        #
        # Do we have a credible number of values to regress?
        #

            # Linear regress the measured Sex Tractor magnitudes and the Gaia magnitudes.
            # Order is dependent then independent variables
            #
            if (len(regGaiaMagList)) > 4:
                results = qLinReg(SEmagList_Gaia,regGaiaMagList)
                gaiaIntercept = results[0]
                gaiaSlope = results[1]
                R2 = round(results[2], 2)
                writeNote("Calibrating measured SE magnitudes against Gaia magnitudes (R-squared = " + str(R2) + ").")

                # Generate Gaia-based regressed values for each lightsource
                for value in SEmagList:
                    adjSEmagList_Gaia.append(round(gaiaIntercept + (gaiaSlope * value),2))

            else:
                gaiaIntercept = 9999
                gaiaSlope = 9999

                for value in SEmagList:
                    adjSEmagList_Gaia.append(" ")

            # Linear regress the measured Sex Tractor magnitudes and the APASS magnitudes.
            if (len(regAPASSmagList)) > 4:
                results = qLinReg(SEmagList_APASS, regAPASSmagList)
                APASSintercept = results[0]
                APASSslope = results[1]
                R2 = round(results[2], 2)
                writeNote("Calibrating measured SE magnitudes against APASS magnitudes (R-squared = " + str(R2) + ").")

                # Generate APASS-based regressed values for each lightsource
                for value in SEmagList:
                    adjSEmagList_APASS.append(round(APASSintercept + (APASSslope * value),2))  

            else:
                APASSintercept = 9999
                APASSslope = 9999

                for value in SEmagList:
                    adjSEmagList_APASS.append(" ")

            # Tell us what the target magnitude is based on catalogs (if available) as well
            # as our guesses based on APSS & Gaia linear regressions.
            writeGap()
            timeStamp("Magnitude of target " + targName + " estimated to be: " )
            writeGap()


            if realtargGaiaMag != "":
                writeSpaced("Based on Gaia catalog entry: " + str(realtargGaiaMag))

            if gaiaIntercept != 9999:
                targCalibSEmagGaia = round(gaiaIntercept + (gaiaSlope * float(lsMagArray[targetLS])),2)            
                writeSpaced("Based on Gaia regression: " + str(targCalibSEmagGaia))

            writeGap()

            if realtargAPASSmag != "":
                writeSpaced("Based on APASS catalog entry: " + str(realtargAPASSmag))

            if APASSintercept != 9999:
                targCalibSEmagAPASS = round(APASSintercept + (APASSslope * float(lsMagArray[targetLS])),2)            
                writeSpaced("Based on APASS regression: " + str(targCalibSEmagAPASS))            

            writeGap()

            # Dump the catalog & regression-adjusted Sex Tractor magnitudes out to a CSV file
            timeStamp("Writing Magnitudes to CSV file.")
            fileNum = len(fileList)
            dirName,fileName = os.path.split(fileList[0])
            csvFile = imgPath.replace(".fit", ".csv")
            srcFile = imgPath.replace(".fit", ".SRC")
            outFile = open(csvFile, "w")
            outFile.write("RA(j2k),Dec(j2k),UTC,Gaia,Gaia Cal. SE,APASS,APASS Cal. SE" + CR)
            
            for index in range(len(SEmagList)):
                outFile.write(prettyRADecList[index] + "," + obsDateList[index] + "," + str(gaiaMagList[index]) + "," +  \
                     str(adjSEmagList_Gaia[index]) + "," + str(APASSmagList[index]) + "," + str(adjSEmagList_APASS[index]) + CR)
    
            outFile.close()
            
            # Clean up the ugly and un-needed source extractor SRC files.
            if os.path.exists(srcFile):
                os.remove(srcFile)

        else:
            writeError("Insufficient values to regress.")

    writeGap()
