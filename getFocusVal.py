# -*- coding: utf-8 -*-
"""
Created on Fri May 26 15:37:42 2023

@author: lgtle


Script aimed at obtaining and storing for further use the value of the focuser's
position for each indicated filterNames. Notice those values may change with seeing
conditions and temperature of the telescope, so that this script should be run
prior to any use of those 'standard' values.



"""

from theSkyLibLL import * 
import argparse
import os

Ra, Dec = getRA_DEC()
filterNames = ["B", "V", "R", "I"]
path_to_data = "./dataTelescope/"

# Setting logs
logName = f"./logs/{time.strftime('[%y-%m-%d_%H-%M-%S]')}FocusVal.log"
timeStamp = logger(timeStamp, logName)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "FF",
                                 description = "Automatized routine of FF acquisition",
                                 epilog = "Designed by LL")

    parser.add_argument("filterNames", type=str, nargs="*", default = ["B", "V", "R", "I"],
                        help = "Names of the required filters. Default : B, V, R, I")
    
    args = parser.parse_args()

    if args.filterNames != None:filterNames = args.filterNames


# Get the zero-based filter wheel

FilterNums = getFilterNums()
filters = [FilterNums[f] for f in filterNames]  # Gets the appropriate index for filters in the filter wheel
num2f = {filters[i]: filterNames[i] for i in range(len(filters))}


# Checks the data repertory exists, otherwise creates it

try:
    readMe = open(path_to_data+"README.txt", "w")
except FileNotFoundError:
    os.mkdir(path_to_data)
    readMe = open(path_to_data+"README.txt", "w")

readMe.write("Last update : " + f"{time.strftime('[%y-%m-%d_%H-%M-%S]')}")
readMe.close()

# Focus routine

TSXSend(f"sky6RASCOMTele.SlewToRaDec({Ra}, {Dec}, 'Here')") # Memorizes original position

for f in filters:
    timeStamp(f"Performing @Focus2 with filter {num2f[f]}...")
    focPos = focus2("Here", f)
    with open(path_to_data+f"focPos{num2f[f]}", "w") as file:
        file.write(str(focPos))


# Identifies focuser motion methods
focPos = TSXSend("ccdsoftCamera.focPosition")
TSXSend("ccdsoftCamera.focMoveIn(1)")
focPos2 = TSXSend("ccdsoftCamera.focPosition")

with open(path_to_data+"focMoveIn", "w") as file:
    if focPos2 > focPos : file.write("+")
    elif focPos2 < focPos : file.write("-")
    else: file.write(".")



