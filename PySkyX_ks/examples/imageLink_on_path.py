#!/usr/bin/env python3

#
# Runs IL on a file or directory.
#
# Written to test a smarter routine designed around Classic Image Link, but will use All Sky 
# if that is what is selected in the GUI.
#
# Can be useful to insert WCS coordinates into the header.
#
# Ken Sturrock
# April 25, 2020
#

from library.PySkyX_ks import *

import time
import sys
import os
import statistics
import glob



# Main Loop Start
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

fileNum = (len(fileList))


counter = 0

print("----------")
timeStamp("Running Image Link on Images.")

while (counter < fileNum):

    print("--------------------------------------------------------------------------------")
    print("Processing image: " + str(counter + 1) + " of " + str(fileNum))
    print("--------------------------------------------------------------------------------")

    imgPath = fileList[counter]

    newPathName = flipPath(imgPath)

    TSXSend("ccdsoftCameraImage.DetachOnClose = 0")
    TSXSend('ImageLink.pathToFITS = "' + newPathName + '"')
    TSXSend('ccdsoftCameraImage.Path = "' + newPathName + '"')
    TSXSend("ccdsoftCameraImage.Open()")

    ilResults = classicIL()
    TSXSend("ccdsoftCameraImage.Close()")

    if "TypeError:" in ilResults :
        print("    ERROR: Image Link Failed.")
        print("    ERROR: " + ilResults)

    else:
        timeStamp("Image Link Successful.")

    counter = counter + 1

print("----------")
timeStamp("Finished.")
sys.exit()





