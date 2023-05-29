# -*- coding: utf-8 -*-
"""
Script aiming at taking Flat Fields for the Telesto at a given exposure time.

Positional parameters  : Original coordinates of the Flat Field region, RA, dec
Optional parameters : exposure time, binning, parameter of the spiral pattern,
as well as a flag which indicates whether the observation is taking place in the 
morning. In this case, order of filters is reversed.

"""
#%% Definitions, parameters
from astropy.io import fits
from theSkyLibLL import *
import numpy as np
import time
import argparse
from sys import exit

# Parameters, to be modified by the user; those are default
expT = 1    # Exposure time in seconds
morning = False  # True for morning; False for dawn 
binning = 1     # binning : 1 for 1x1, 2 for 2x2

RA_FF, dec_FF = getRA_DEC() # Coordinates of the Flat Field area : default at present

lbound = 25000  # Bounds for median exposure of FFs, in DN
ubound = 30000

# Const params
filterNames = ["B", "V", "R", "I"]
FilterNums = getFilterNums()

constA = 0.05      # Parameter of spiral pattern
focDefault = 2700       # Default position of the focuser

#%% Parse the arguments

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "FF",
                                 description = "Automatized routine of FF acquisition",
                                 epilog = "Designed by LL")

    parser.add_argument("RA", type=float, nargs="?", default = RA_FF)
    parser.add_argument("declination", type=float, nargs="?", default = dec_FF)
    parser.add_argument("-e", "--expT", type = float, help="Exposure Time")
    parser.add_argument("-m", "--morning", action="store_true", help="Is it morning?")
    parser.add_argument("-b", "--binning",type = int,  help="1 for 1x1, 2 for 2x2")
    parser.add_argument("-s", "--spiral", type=float, help="Parameter of spiral pattern")  
    parser.add_argument("-l", "--lbound",type=int, help="Lower bound for the median exposure")
    parser.add_argument("-u", "--ubound", type=int, help="upper bound for the median exposure")  
    parser.add_argument("-f", "--filters", type=str, nargs='+', help="Filters from blue-er to red-er (Default : B V R I)")    
    parser.add_argument("--focuser", type=int, help="Default value for focuser position if not stored in dataTelescope. "+
                        "Default set to 2700")
    
    args = parser.parse_args()
    
    RA_FF = args.RA                           
    dec_FF = args.declination
   
    if args.binning != None: binning = args.binning
    if args.expT != None:expT = args.expT
    if args.spiral != None:constA = args.spiral
    if args.morning != None:morning = args.morning
    if args.lbound != None:lbound = args.lbound
    if args.ubound != None:ubound = args.ubound
    if args.filters != None:filterNames = args.filters
    if args.focuser !=None : focDefault = args.focuser
    if ubound <= lbound : 
        print("Exposure upper bound lower than exposure lower bound. The two "+
              "parameters were interverted")
        ubound, lbound = lbound, ubound         # Swaps the bounds
    elif ubound == lbound:
        raise ValueError("Exposure bounds cannot be equal")
        
#%% PROCESSING OF PARAMETERS AFTER PARSE


#Organize filters variables
filters = [FilterNums[f] for f in filterNames]  # Gets the appropriate index for filters in the filter wheel
num2f = {filters[i]: filterNames[i] for i in range(len(filters))}


# Setup logs 
logName = f"./logs/{time.strftime('[%y-%m-%d_%H-%M-%S]')}FF.log"
timeStamp = logger(timeStamp, logName)
console = logger(print, logName)

# Get the focuser position for each filter
focPos = dict()
for f in filterNames:
    try:
        with open(path_to_data+f, "r") as file:
            focPos[f] = int(file.read())
    
    except FileNotFoundError:
        console(f"WARNING : Focuser position for filter {f} not stored in data. "+
                "Focpos set to default value {focDefault}")
        focPos[f] = focDefault
    except ValueError:
        console(f"ERROR : Incorrect focPos value stored in data for filter {f}. "+
                "Focpos set to default value {focDefault}")
        focPos[f] = focDefault
    except:
        console(f"ERROR : Unknown error with focPos value stored in data for filter {f}. "+
                "Focpos set to default value {focDefault}")
        focPos[f] = focDefault


try:
    with open(path_to_data+"focMoveIn", "r") as file:
        focMoveIn = file.read()
except:
    console(f"WARNING : focMoveIn direction was not determined beforehand to running this script. "+
            "Determining it now.")
    
    focPos = TSXSend("ccdsoftCamera.focPosition")
    TSXSend("ccdsoftCamera.focMoveIn(1)")
    focPos2 = TSXSend("ccdsoftCamera.focPosition")
    if focPos2 > focPos : focMoveIn = "+"
    elif focPos2 < focPos : focMoveIn = "-"
    else: 
        console("ERROR : focMoveIn direction could not be determined. Aborting...")
        sys.exit()
    
    try:
        with open(path_to_data+"focMoveIn", "w") as file:
            file.write(focMoveIn)
    except:
        console("WARNING : focMoveIn could not be written to telescope data. Check "+
                "the indicated path to the telescope data folder")

if focMoveIn not in ["+", "-"]:
    console("ERROR : Incorrect focMoveIn direction stored in data. Aborting...")
    sys.exit()
         
# --------------------------DEFINITIONS-----------------------------------

def dataFits(path:str, file=""):
    
    """Returns header and data of a specified FITS file"""
    
    full_path = path+file
    HDUl = fits.open(full_path)
    
    data = HDUl[0].data
    header = HDUl[0].header
    
    return data, header


def medExp(full_path):
    
    """Returns the median exposure of an image stored at the specified location"""
    
    data, header = dataFits(full_path)
    return np.median(data)


def check_exposure(test_pic, l = lbound, u = ubound, verbose = False):
    
    """Check the median exposure of the given image to be within bounds in source.
    """
    
    exp = medExp(test_pic)
    if verbose:console(f"Measured exposure : {exp}")
    
    if l >= exp : result = -1       # exposure too low
    elif u <= exp : result = 1      # exposure too high
    else : result = 0               # exposure ok
    
    
    return result


def take_and_check_exp(filtre, rem = True, verbose = False):
    
    """Takes a picture and analyse its median exposure
    If the test fails and rem flag is on, the picture is DELETED"""
    
    test_pic = TakePic(expT, filtre, binning)
    if verbose: console("Test picture taken and saved at : " + test_pic)
    result =  check_exposure(test_pic, verbose=verbose)

    if result != 0 : 
        if rem:
            RemovePic(test_pic) #Deletes bad pictures
            if verbose : console("Test picture deleted at : " + test_pic)
            
    return result

def spiralCoords(theta, constA):
    
    """Parametrization of a spiral"""
    
    r = constA*theta
    RA = r*np.cos(theta)
    dec = r*np.sin(theta)
    
    return RA, dec


#%%
# --------------------------MAIN-----------------------------------

if __name__ == "__main__":
    
    
    if morning: filters.reverse()       # Sets the filters in right order depending
                                        # on time
    TSXSend("ccdsoftCamera.Frame = 4;")
    
    timeStamp(f"FF.py launched with following parameters:\n\n"+
      f"(RA, dec) coordinates : ({RA_FF}, {dec_FF})\n"+
      f"Time : {'morning' if morning else 'dawn'}\n"+
      f"Exposure time : {expT}\n" +
      f"Median exposure comprised between {lbound} and {ubound} DN\n"+ 
      f"Spiralic pattern parameter : {constA}\n\n" + 
      f"Slewing to the start location...\n")
    
    
    number_FFs = dict()     # Counter of FF by filter
    
    for f in filters:
        
        
        
        slewTo(RA_FF, dec_FF)                       # Moves to start
        setFocPos(focPos[num2f[f]])                 # Moves focuser appropriately
    
        timeStamp(f"Waiting for sky illumination to reach target level...")
        start = False
        skip = False
        
        while not start:   # Waits for the correct illumination
            expStatus = take_and_check_exp(f, verbose=True)
            
            if expStatus == 0:
                start = True
                number_FFs[f] = 1       # keep pic from take_and_check
            elif (expStatus == 1 and morning) or (expStatus == -1 and not morning):
                start = True 
                skip = True             # Bad timing, this filter has no chance
                console("Exposure inappropriate, switching to next filter...")
                number_FFs[f] = 0       # Pic from take_and_check was removed
                
            else:
                time.sleep(5)           # All good, wait a little
                            
        if skip : continue              # Skips to next filter, otherwise the
                                        # following code is executed
        timeStamp("Flat field acquisition started for filter " + num2f[f])
        
        step = np.pi/6  # Step of the spiralic pattern
        theta = step    # Parameters of the spiral, r = a*theta
    
        while take_and_check_exp(f) == 0 :        # Takes a Flat Field and check exposure
        
            dRA, dDec = spiralCoords(theta, constA)
            slewTo(RA_FF+dRA, dec_FF + dDec)    # Moves the telescope along the spiralic pattern
        
            theta += step
            number_FFs[f] += 1
    
        timeStamp(num2f[f] + f" filter : {number_FFs[f]} pictures taken")
        
    timeStamp("Flat Field Acquisition complete.")
    TSXSend("ccdsoftCamera.Frame = 1")      # Sets back the frame to default
    
