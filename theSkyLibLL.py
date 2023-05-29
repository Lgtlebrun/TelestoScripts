# -*- coding: utf-8 -*-


"""
This library aims at allowing users of TheSkyX to send entire JS scripts to the
software. It completes and uses extensively some previous work by Ken Sturrock.

FUNCTIONS : 
    
    checkScript
    cleanScript   
    dataFits
    focus2
    focus3
    getFilter_Nums
    getRA_DEC
    isVisible
    logger
    parse2script
    readJS
    RemovePic
    slewTo
    slewVar    
    TakePic
    TSXSendScript
    
LL

"""

import os
import re
import time
from PySkyX_ks.library.PySkyX_ks import *
from astropy.io import fits


path_to_JS = "./JS_scripts/"
path_to_logs = "./logs/"
path_to_data = "./dataTelescope/"


def dataFits(path:str, file=""):
    
    """Returns header and data of a specified FITS file"""
    
    full_path = path+file
    HDUl = fits.open(full_path)
    
    data = HDUl[0].data
    header = HDUl[0].header
    
    return data, header





def checkScript(script : str, name = ""):
    """Checks if all parameters were correctly filled in the script"""
    
    if not ('$' in script):
        return True
    else:
        idx = script.find('$')
        param = script[idx +1 : idx +3].strip()
        param = re.sub("[^0-9]", "", param) #only keeps the number of the param
        print("ERROR : parameter " + param + " not filled in script " + name)
        return False
        
def cleanScript(script :str):
    """Removes comments and useless whitespaces from script to make it fit
    the TSX 4096 bytes limitation and optimize readout time"""
    
    #Remove comments
    idxComment = script.find('//')
    
    while idxComment > 0 :          # Find will return -1 if not found
        idxEndl = script.find('\n', idxComment)
        script = script[:idxComment] + script[idxEndl:]
        idxComment = script.find('//')
        
    #Remove Header
    idxHeader = script.find('/*')
    while idxHeader >= 0:
        idxEnd = script.find('*/', idxHeader) + 1
        script = script[:idxHeader] + script[idxEnd+1:]
        idxHeader = script.find("/*")
    
    #Remove whitespaces
    idxWhite = script.find("\n\n")
    while idxWhite > 0:
        script = script[:idxWhite] + script[idxWhite+1:]
        idxWhite = script.find("\n\n")
    
    return script.strip()
        


def CLS(target, filterNum):
    """Executes a CLS to the specified target e.g. 'Venus', with given filter"""
    
    slewTarget(target)
    return TSXSendScript("ClosedLoopSlew.js", target, filterNum) #returns error number


def focus2(target, filterNum):
    
    """Rewritten version of the atFocus2 routine, getting rid of all the junk by
    our messiah the great Ken Sturrock. 
    """
    
    #Initialize logs
    logPath = path_to_logs+f"{time.strftime('[%y-%m-%d_%H-%M-%S]')}Focus2.log"
    try :
        logFile = open(logPath, "w")
        logFile.close()
    except :
        logPath = "./" + f"{time.strftime('[%y-%m-%d_%H-%M-%S]')}Focus2.log"
    
    logtimeStamp = logger(timeStamp, logPath)
    logwriteNote = logger(writeNote, logPath)
    
    #Main routine
    
    logtimeStamp("Focusing with @Focus2.")
    if targHA(target) < 0.75 and targHA(target) > -0.75:
        writeNote("Target is near the meridian.")
        if TSXSend("SelectedHardware.mountModel") !=  "Telescope Mount Simulator":
            TSXSend('sky6RASCOMTele.DoCommand(11, "")')
            if TSXSend("sky6RASCOMTele.DoCommandOutput") == "1":
                TSXSend('sky6RASCOMTele.Jog(420, "E")')
                logwriteNote("OTA is west of the meridian pointing east.")
                logwriteNote("Slewing towards the east, away from meridian.")


            else:
                TSXSend('sky6RASCOMTele.Jog(420, "W")')
                logwriteNote("OTA is east of the meridian, pointing west.")
                logwriteNote("Slewing towards the west, away from meridian.")

 
    if TSXSend("SelectedHardware.filterWheelModel") != "<No Filter Wheel Selected>":
        TSXSend("ccdsoftCamera.filterWheelConnect()")	
        TSXSend("ccdsoftCamera.FilterIndexZeroBased = " + str(filterNum)) 
        
        
    
    result = TSXSend("ccdsoftCamera.AtFocus2()")

    if "Process aborted." in result:
        logtimeStamp("Script Aborted.")
        sys.exit()

    if "rror" in result:
    # Bad stuff can happen sometimes, let's try again soon.
        logtimeStamp("@Focus2 failed: " + result)
        focPos = 2700 if filterNum != 0 else 3000


    else:
        TSXSend("sky6ObjectInformation.Property(0)")
        
        focPos = TSXSend("ccdsoftCamera.focPosition")
        logtimeStamp("@Focus2 success.  Position = " + TSXSend("ccdsoftCamera.focPosition") + ". Star = " \
                + TSXSend("sky6ObjectInformation.ObjInfoPropOut"))
        
    logtimeStamp("Slewing back to target.")
    CLS(target, filterNum)  #Goes back to target
    return focPos


def focus3(expT, filtre):
    """Focus using @focus3 routine via AtFocus3 JS script"""
    
    return TSXSendScript("AtFocus3.js", f, expT)





def getFilterNums():
    """Obtains the zero-based indices of the filter wheel"""
    nums = dict()
    i = 0
    while i >= 0:
        msg = TSXSend(f"ccdsoftCamera.szFilterName({i})")
        if msg == "" : i = -1
        else :
            fName = msg[:msg.find("(")].strip()
            nums[fName] = i
            i += 1
    return nums
        
    

def getRA_DEC(target = "None"):
    """Returns current Right ascension and declination of the telescope"""

    msg = TSXSendScript("getRA_DEC.js", target)

    if "rror" in msg :
        print("Error : object not found")
        return 0,0

    
    coords = msg.split("&")
    return coords[0], coords[1]



def isVisible(target):
    """Returns true if target is currently above horizon"""
    
    return TSXSendScript("isVisible.js", target)


def logger(func, path="log.log"):
    """Loads output of printing function 'func' to both normal output and log file
    Usage : func = log(func, path)
    
    WARNING : Due to lazyness from my side, the new 'func' only tolerates one 
    positional argument, a.k.a. the message to be displayed and logged
    WARNING 2 : Of course, output messages sent via func by imported functions will
    NOT be logged --> I shall use the logging module next time"""
    def wrapper(msg):
        with open(path, 'a') as file:
            func(msg, file=file)
        func(msg)
    return wrapper


def parse2script(script : str, *args):
    """ Parse the (array-like, ordered) params to the script at places indicated
    with $XXX, XXX being the index of the parameter to parse"""
    
    for i, arg in enumerate(args):
       script = script.replace(f"${i}", str(arg))
   
    return script
    

def readJS(name, path=path_to_JS):
    """Reads a .js script and returns it as a string"""
    
    try:
        with open(path+name, 'r') as file:
            script = file.read()
            return script
    except:
        script = ""
        print("ERROR : file " + name + " not found at path " + path)
        return script
    


def RemovePic(full_path):
    """Removes an image at given location"""    
    os.remove(full_path)
    

def setFocPos(focPos):
    currentFocPos = int(TSXSend("ccdsoftCamera.focPosition"))
    
    if focPos > currentFocPos:
        
        return TSXSend(f"ccdsoftCamera.focMoveOut({focPos-currentFocPos})")
    elif focPos < currentFocPos:
        
        return TSXSend(f"ccdsoftCamera.focMoveIn({currentFocPos-focPos})")


def slewTo(RA, dec):
    """Slew the telescope to given Right Ascension (RA) and declination (dec) 
    using Terry R. Friedrichsen script Slew.js"""

    timeStamp(f"Slewing to {RA}, {dec}") 
    return TSXSendScript("SlewTo.js", RA, dec)

def slewVar(dRA, dDec):
    """Slew the telescope by a variation of RA and dec from current target (in degrees)"""
    
    RA, dec = getRA_DEC()
    return slewTo(float(RA) + dRA, float(dec) + dDec)

def slewTarget(target):
    """ Slew the telescope to a target referenced by name, e.g. 'Venus' """
    
    RA, dec = getRA_DEC(target)
    return slewTo(RA, dec)
    

def TakePic(exposure, filtre, binning):
    """Take an image with the Imager. Uses TakeImage.js script"""
    
    return TSXSendScript("TakeImage.js", "Imager", exposure, "'NA'", filtre, binning)

        
def TSXSendScript(name, *args, path=path_to_JS,  clean = True):
    """Sends a script JS to TSX via Ken Sturrock library PySkyX_ks. 
    *args : parameters to parse to the script"""
    
    script = parse2script(readJS(name, path), *args)
    
    if clean : script = cleanScript(script)
    
    if checkScript(script, name):       # verifies if no parameter is missing
        return TSXSend(script)          # Important to return the value

    

