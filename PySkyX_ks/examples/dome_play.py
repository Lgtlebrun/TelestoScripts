#!/usr/bin/env python3
#

from library.PySkyX_ks import *

if (TSXSend("SelectedHardware.domeModel") != "<No Dome Selected>"):
    timeStamp("Dome Detected")



    domeConnect()

    domeUnpark()

    domeFindHome()



    if (domeIsConnected() == "Connected") & (domeIsCoupled() == "Coupled"):
        writeNote("The dome is connected and coupled to the mount.")


        domeGoTo(180)

        domeSync()

        domeOpenOrClosed()

        domeOpen()

        domeClose()

        domeOpenOrClosed()

        domePark()

        domeDisconnect()
