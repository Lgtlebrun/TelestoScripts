#!/usr/bin/env python3

#
# Ken Sturrock
# June 09, 2021
#

from library.PySkyX_ks import *

import sys
import glob



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
keyWord = input("Please enter Keyword Name: ")
value = input("Please enter keyword value: ")

counter = 0

print("----------")
timeStamp("Adding FITS Kerywords & values to images.")

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

    TSXSend('ccdsoftCameraImage.setFITSKeyword("' + keyWord + '", "' + value +'")')

    TSXSend("ccdsoftCameraImage.Save()")

    TSXSend("ccdsoftCameraImage.Close()")

    counter = counter + 1

print("----------")
timeStamp("Finished.")

