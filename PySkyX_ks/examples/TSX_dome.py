#!/usr/bin/env python3

#
# Dome control routines from Rodolphe Pineau
#
# March 26, 2021
#

import sys
import math
import time

import PySkyX_ks.library.PySkyX_ks as PySkyX_ks


class TSXDome(object):

    __Host = None
    __Port = 3040
    __GotoAz = 0
    __debug = False

    def __init__(self, Host = "127.0.0.1", Port = 3040):
        self.__Host = Host
        self.__Port = Port

    def enableDebug(self, bEnable = False):
        self.__debug = bEnable

    def domeConnect(self):
        try:
            Err = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.Connect()")
            if Err.find("Error") != -1:
                raise Exception("Error", "Can't connect to dome")
        except Exception as e:
            raise e

    def domeDisconnect(self):
            Err = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.Disconnect()")


    def Goto(self, Az, El = 90):
        realAz = Az % 360
        Err = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.GotoAzEl(%s, %s)" % (realAz, El))
        self.__GotoAz = realAz
        if self.__debug:
            print("Err = %s" % Err)
            print("Goto Az = %s" % self.__GotoAz )
        return Err

    def Open(self):
        Err = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.OpenSlit()")
        if self.__debug:
            print("Err = %s" % Err)
            print("Opening slit( Err= %s ) " % Err )
        return Err

    def Close(self):
        Err = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.CloseSlit()")
        if self.__debug:
            print("Err = %s" % Err)
            print("Closing slit( Err= %s ) " % Err )
        return Err

    def FindHome(self):
        Err = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.FindHome()")
        if self.__debug:
            print("Err = %s" % Err)
            print("Finding home ( Err= %s ) " % Err )
        return Err

    def Park(self):
        Err = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.Park()")
        if self.__debug:
            print("Err = %s" % Err)
            print("Parking dome ( Err= %s ) " % Err )
        return Err

    def UnPark(self):
        Err = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.Unpark()")
        return Err

    def IsOpenComplete(self):
        bIsOpenComplete = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.IsOpenComplete")
        if self.__debug:
            print("bIsOpenComplete = %s " % bIsOpenComplete )
        if(bIsOpenComplete == "0"):
            return False
        else :
            return True

    def IsCloseComplete(self):
        bIsCloseComplete = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.IsCloseComplete")
        if self.__debug:
            print("bIsCloseComplete = %s " % bIsCloseComplete )
        if(bIsCloseComplete == "0") :
            return False
        else :
            return True
        return False

    def IsFindHomeComplete(self):
        bIsFindHomeComplete = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.IsFindHomeComplete")
        if self.__debug:
            print("[IsFindHomeComplete] bIsFindHomeComplete = %s" % bIsFindHomeComplete )

        if(bIsFindHomeComplete == "0"):
            return False
        else :
            return True

    def IsGotoComplete(self):
        bIsGotoComplete = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.IsGotoComplete")
        if self.__debug:
            print("[IsGotoComplete] bIsGotoComplete = %s" % bIsGotoComplete )

        if(bIsGotoComplete == "0"):
            return False
        else :
            return True

    def IsParkComplete(self):
        bIsParkComplete = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.IsParkComplete")
        if self.__debug:
            print("[IsParkComplete] bIsParkComplete = %s" % bIsParkComplete )

        if(bIsParkComplete == "0"):
            return False
        else :
            return True

    def IsUnparkComplete(self):
        bIsUnparkComplete = PySkyX_ks.TSXSendRemote("%s:%d" % (self.__Host, self.__Port), "sky6Dome.IsUnparkComplete")
        if self.__debug:
            print("bIsUnparkComplete = %s " % bIsUnparkComplete )
        if(bIsUnparkComplete == "0"):
            return False
        else :
            return True


def main():

    dome = TSXDome()
    # dome.enableDebug(True)

    try:
        dome.domeConnect()
    except Exception as e:
        print("Error connecting to dome : %s" % e)
        dome.domeDisconnect()
        sys.exit(1)

    print("Unparking dome")
    dome.UnPark()
    while(True):
        if dome.IsUnparkComplete():
            break
        time.sleep(1)

    print("Dome unparked")

    print("Homing dome")
    dome.FindHome()
    while(True):
        if dome.IsFindHomeComplete():
            break
        time.sleep(1)

    print("Dome is at home")

    print("Opening dome")
    dome.Open()
    while(True):
        if dome.IsOpenComplete():
            break
        time.sleep(1)

    print("Shutter openned")

    print("Goto 270")
    dome.Goto(270, 90);
    while(True):
        if dome.IsGotoComplete():
            break
        time.sleep(1)

    print("Goto 270 done");

    print("Goto 180")
    dome.Goto(180, 90);
    while(True):
        if dome.IsGotoComplete():
            break
        time.sleep(1)

    print("Got 180 done");

    print("Parking dome")
    dome.Park()
    while(True):
        if dome.IsParkComplete():
            break
        time.sleep(1)

    print("Dome is parked")


    print("Closing dome")
    dome.Close()
    while(True):
        if dome.IsCloseComplete():
            break
        time.sleep(1)

    print("Shutter closed")


    dome.domeDisconnect()

if __name__ == '__main__':
    sys.exit(main())


