# -*- coding: utf-8 -*-
"""
Created on Tue May 23 11:52:11 2023

Automatizes observation of celestial object with defocus

@author: LL
"""

from theSkyLibLL import *
from astropy.io import fits
import numpy as np
import argparse
import logging
import sys
import time


# Initial parameters

expT = 1                # Exposure time
defocusInit = 0             # Number of steps of the focuser out of focus
                        # Step of TELESTO : 1.59 µm
loop = True             # Shall we loop while target is visible                                  
binning = 1

fullWell = 90000    # e-
gain = 1.4          # e-/count

maxCounts = fullWell/gain


target = "Venus"
referenceStar = "TYC 1914-1694-1"


filterNames = ["B", "V", "R", "I"]


# %% Parse the arguments

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "FF",
                                 description = "Automatized routine of FF acquisition",
                                 epilog = "Designed by LL")

    parser.add_argument("target", type=str,help="Target to observe")
    
    parser.add_argument("-r", "--reference" ,type=str,help="Reference star")
    parser.add_argument("-e", "--expT", type = float, help="Exposure Time")
    parser.add_argument("-b", "--binning",type = int,  help="1 for 1x1, 2 for 2x2")
    parser.add_argument("-f", "--filters", type=str, nargs='+', help="Filters from blue-er to red-er (Default : B V R I)")    
    parser.add_argument("-d", "--defocus", type=int, help="Number of steps to defocus")
    parser.add_argument("-o", "--once", action="store_false", help="Shall we take only one pic?")
    args = parser.parse_args()
    
    target = args.target
   
    if args.binning != None: binning = args.binning
    if args.expT != None:expT = args.expT
    if args.filters != None:filterNames = args.filters
    if args.reference != None : referenceStar = args.reference
    if args.defocus != None : defocusInit = args.defocus
    if args.once != None : loop = args.once


# Setup logs 

logName = f"./logs/{time.strftime('[%y-%m-%d_%H-%M-%S]')}{target}.log"
timeStamp = logger(timeStamp, logName)
console = logger(print, logName)


# Processing parsed arguments

timeStamp(f"Routine launched with following initial parameters:\nExposure : {expT} s\n" +
      f"defocus : {defocusInit} steps\n" + f"Target : {target}\nReference star : {referenceStar}\n"+
      f"Binning : {binning}x{binning}\n" + f"Filters : {', '.join(filterNames)}" +
      f"\n{'Taking pictures as long as target is visible.' if loop else 'Taking one picture only'}")

FilterNums = getFilterNums()
refCoords = getRA_DEC(referenceStar)        # Coords of reference star

filters = [FilterNums[f] for f in filterNames]  # Gets the appropriate index for filters in the filter wheel
num2f = {filters[i]: filterNames[i] for i in range(len(filters))}


# ------------ DEFINITIONS -----------------


def TakePicWithDefocus(expT, defocus, numFil):
    
    """Takes a picture of target with a defocus"""  
    
    TSXSend(f"ccdsoftCamera.focMoveOut({defocus})")     #defocus
    return TakePic(expT, numFil, binning)
   
    
def checkSaturation(pic):
    
    """Checks if an image is saturated with bound under the analytical saturation"""
    
    tol = 1000
    data, header = dataFits(pic)
    
    for val in np.nditer(data):
        if val > maxCounts-tol:
            return False
    return True



# -------- WAIT FOR TARGET TO RISE ABOVE HORIZON ---------------

console(f"Waiting for {target} to show above horizon...")

while not isVisible(target):
    time.sleep(5)

timeStamp("Target has shown up. Slewing to target...")

#--------- DOUBLE CHECK OF INITIAL PARAMETERS ------------

TSXSend("ccdsoftCamera.Frame = 1")      # Sets back the frame to light

setFocPos(3000)
defocus = dict()
    
for f in filters:
        doubleCheck = False
        
        while not doubleCheck :
            
            slewTarget(target)              # Goes to target
            defocus[f] = defocusInit
            pic = TakePicWithDefocus(expT, defocus[f], f)
            TSXSend(f"ccdsoftCamera.focMoveIn({defocus[f]})")
        
            if not checkSaturation(pic) : 
                defocus[f] += 10                # Increase defocus if pic saturated
                timeStamp(f"Filter {num2f[f]} saturated, defocus increased by 10")
            else : doubleCheck = True
            

console(f"\nDefocus after double check : ")
for f in filters:
    console(f"Filter {num2f[f]} : {defocus[f]}")  #display changes


#---------- MAIN SEQUENCE ------------

while isVisible(target and loop):
# Focus on reference star and acquire sequence
    #CLS(referenceStar, 0)
    slewTarget(referenceStar)
    for f in filters:
        
        pic = TakePic(expT, f, binning)
        timeStamp(f"Picture of reference star taken in filter {num2f[f]} at path {pic}")
    
    
    
    for f in filters :
        slewTarget(target)      # Slew to target 
        TakePicWithDefocus(expT, defocus[f], f)     # "here" avoids CLS again
        timeStamp(f"Picture of target taken in filter {num2f[f]} at path {pic}")
        
        TSXSend(f"ccdsoftCamera.focMoveIn({defocus[f]})")


#Close logs

for handler in log.handlers:
    handler.close()
    log.removeFilter(handler)


                        
