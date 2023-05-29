#!/usr/bin/env python3
#
# Generates codes for the full calibration feature.
#

from library.PySkyX_ks import *

import time
import sys
import os


camModel = TSXSend("SelectedHardware.cameraModel")
binning =  (TSXSend("ccdsoftCamera.BinX") + "x" + TSXSend("ccdsoftCamera.BinY"))
filName = TSXSend("ccdsoftCamera.szFilterName(" + str(TSXSend("ccdsoftCamera.FilterIndexZeroBased")) + ")")
expTime = TSXSend("ccdsoftCamera.ExposureTime")
otaDesc = TSXSend('ccdsoftCamera.PropStr("m_csTeleDescription")')
ccdTemp = TSXSend("ccdsoftCamera.TemperatureSetPoint")
exactRGName = (otaDesc + " " + camModel + " " + filName  + " " + binning + " " + ccdTemp + " " + expTime).replace(" ", "_")
scaleRDName = (otaDesc + " " + camModel + " " + filName  + " " + binning + " " + "Scale").replace(" ", "_")

print("Exact Reduction Group Name: " + exactRGName)
print("Scaled Reduction Group Name: " + scaleRDName)

