#!/usr/bin/env python3

#
# This is under development
#

# September 7, 2020
#

from library.PySkyX_ks import *

import time
import sys
import os

riseTimes = []
transitTimes = []
setTimes = []
HAs = []
unitsUp = []
imageStartTimes = []
imageStopTimes = []

targets = sys.argv

del targets[0]

numTargets = len(targets) 


# Get times for the Sun

results = targRiseSetTimes("Sun", "-15")

sunRise,sunTransit,sunSet=results.split(" -> ")

hours,minutes=sunRise.split(":")
hours = int(hours)
minutes = int(minutes)
results = HMSToDec(hours, minutes, 0)
sunRise = round(results[3], 1)


hours,minutes=sunSet.split(":")
hours = int(hours)
minutes = int(minutes)
results = HMSToDec(hours, minutes, 0)
sunSet = round(results[3], 1)

for target in targets:

    if targExists(target) == "Yes":


        TSXSend("sky6StarChart.Find('" + target + "')")


        TSXSend("sky6ObjectInformation.Property(70)")
        objHA = round(float(TSXSend("sky6ObjectInformation.ObjInfoPropOut")),1)
        HAs.append(objHA)


        
        results = targRiseSetTimes(target, str(30))

        riseTime,transitTime,setTime=results.split(" -> ")
        
        hours,minutes=riseTime.split(":")
        hours = int(hours)
        minutes = int(minutes)
        results = HMSToDec(hours, minutes, 0)
        riseTime = round(results[3], 1)

        hours,minutes=transitTime.split(":")
        hours = int(hours)
        minutes = int(minutes)
        results = HMSToDec(hours, minutes, 0)
        decTime = round(results[3], 1)

        hours,minutes=setTime.split(":")
        hours = int(hours)
        minutes = int(minutes)
        results = HMSToDec(hours, minutes, 0)
        setTime = round(results[3], 1)


        # You now have to adjust the up time to fit within dark hours.
        
        if riseTime < sunSet:
            if objHA
            
           imageStartTime = sunSet

                

        Up = round((setTime - riseTime), 1)

        

        if Up < 0:
            Up = Up + 24

        unitsUp.append(Up)
        riseTimes.append(riseTime)
        transitTimes.append(decTime)
        setTimes.append(setTime)
        imageStartTimes.append(imageStartTime)





    else:
        print("    ERROR: " + target + " not found in SkyX database.")




# Sort the values based on transit time. May have to do something to compensate for time reset at zero.
#

zippedInList = zip(HAs, transitTimes, riseTimes, setTimes, targets, unitsUp, imageStartTimes)
zippedOutList = zip(*sorted(zippedInList, reverse=True))
HAs_s, transitTimes_s, riseTimes_s, setTimes_s, targets_s, unitsUp_s, imageStartTimes_s = map(list, zippedOutList )


print("")
print("Target\tHA\tRise\tTrans\tSet\tUp\tImStart")
print("------\t--\t----\t-----\t---\t--\t-------")

for index,target in enumerate(targets_s):

    print(target + "\t" + str(HAs_s[index]) + "\t" + str(riseTimes_s[index]) + "\t" \
          + str(transitTimes_s[index]) + "\t" + str(setTimes_s[index]) + "\t" + str(unitsUp_s[index]) \
          + "\t" + str(imageStartTimes_s[index]))






