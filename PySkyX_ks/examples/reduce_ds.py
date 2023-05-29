#!/usr/bin/env python3

#
# This script is meant to tear apart the CSV created by
# the ds_analyze.py script. It will average out duplicate
# measurements, add in the RA+Dec Name and then grade
# the measurement. 
#
# This version was modified for submissions to the Webb Society.
#
# Ken Sturrock
# December 17, 2022
#

from library.PySkyX_ks import *

import sys
import os
import csv
import operator
import statistics

def calcCircDif(value1, value2):
    return 180 - abs(abs(float(value1) - float(value2)) - 180)

def avgMeasures(PAs, Seps, priRAs, priDecs, secRAs, secDecs, gaps):
#
# Takes a list containing PAs, calculates medians
#
    observs = len(PAs)

    normPADifs = []
    secondSeps = []
    secondPAs = []
    thirdSeps = []
    thirdPAs = []

    if (observs == 0) or ("X" in PAs):
        print("    ERROR: No PA supplied.")
        return "noPA"

    medianSep = statistics.median(Seps)
    sdSep = statistics.pstdev(Seps)

    medianPA = circularAverage("median", PAs)
    
    for PA in PAs:
        normPADifs.append(calcCircDif(0, PA))

    sdPAs = statistics.pstdev(normPADifs)


    if (sdSep > 10):
        # If the SD is large, it implies that we probaby have some "way out there" outliers.
        #
        # This does outlier rejection based on the standard deviation of the observations' separations
        # because the separation tends to be REALLY whacked if the routine chases an arborial rodent.
        #
        timeStamp("Large-scale outlier rejection:")
            
        for index in range(len(PAs)):  
            if (Seps[index] > (medianSep + (sdSep))) or (Seps[index] < (medianSep - (sdSep))):
                print("           Observation " + str(index) + " rejected as an outlier (S).")
            
            else:
                secondSeps.append(Seps[index])
                secondPAs.append(PAs[index])
    else:
        #
        # If the starting SD isn't large, then just skip to stage 2.
        secondSeps = Seps
        secondPAs = PAs

    # recalculate the basic PA & Sep stats based on the survivors.
    medianSep = statistics.median(secondSeps)
    sdSep = statistics.pstdev(secondSeps)

    normPADifs = []

    medianPA = circularAverage("median", secondPAs)
    
    for PA in secondPAs:
        normPADifs.append(calcCircDif(0, PA))

    sdPAs = statistics.pstdev(normPADifs)

    timeStamp("Small-scale outlier rejection:")

    # Do the outlier rejection again based on both PA and separation.
    for index in range(len(secondPAs)):  
        if (secondSeps[index] > (medianSep + (1.5 * sdSep))) or (secondSeps[index] < (medianSep - (1.5 * sdSep))):
            print("           Observation " + str(index) + " rejected as an outlier (S).")
            
        elif (calcCircDif(medianPA, secondPAs[index]) > (1.5 * sdPAs)):
            print("           Observation " + str(index) + " rejected as an outlier (P).")

        else:
            print("           Observation " + str(index) + " accepted.")
            thirdSeps.append(secondSeps[index])
            thirdPAs.append(secondPAs[index])

    # Make sure that at least one star passed through the above gauntlet. If not, report noPA so that
    # it can get lumped into the bad stars count.
    if (len(thirdSeps) > 0):

        # Re-run the stats on the second wave of survivors for reporting down stream
        medianSep = statistics.median(thirdSeps)
        medianPA = circularAverage("median", thirdPAs)
    
        sdSep = statistics.pstdev(thirdSeps)
    
        normPADifs = []
    
        for PA in thirdPAs:
            normPADifs.append(calcCircDif(0, PA))
    
        sdPAs = statistics.pstdev(normPADifs)

        observs = len(thirdPAs)
        medianPA = round(medianPA,2)
        medianSep = round(medianSep,2)
        sdPAs = round(sdPAs, 2)
        sdSep = round(sdSep, 2)
        finalPriRA = statistics.median(priRAs)
        finalPriDec = statistics.median(priDecs)
        finalSecRA = statistics.median(secRAs)
        finalSecDec = statistics.median(secDecs)
        finalGap = statistics.median(gaps)

        return str(medianPA) + "; " + str(medianSep) + "; " + str(observs) + "; " + str(sdPAs) + "; " + str(sdSep) \
                + "; " + str(finalPriRA) + "; " + str(finalPriDec) + "; " + str(finalSecRA) + "; " + str(finalSecDec) + "; " + str(finalGap)
    else:
        return "noPA"

# Main Program Start ###########################

badStars = 0
target = []
imagePAs = []
imageSeps = []
targWDSs = []
obsTD = []
priRAs = []
priDecs = []
secRAs = []
secDecs = []
catPAs = []
catSeps = []
comps = []
gaps = []
targSet = set()
uniqueTargs = []
catPA = "NA"
catSep = "NA"
CR = "\n"

#
# Check for and platform rectify the path.
# It isn't necessary here, but old habits die hard.
#
if (len(sys.argv) == 1):
    timeStamp("ERROR. Please specify CSV file to process.")
    sys.exit()

fileName = sys.argv[1]

newPathName = flipPath(fileName)

dirName,fileName = os.path.split(newPathName)

dirName = dirName + "/"

#
# Read through the CVS and put the values into lists
#
# The "Set Trick" is used to create a unique list of targets
# which are then turned back into a list for consistant 
# handling.
#
print("----------")
timeStamp("Reading file: " + newPathName)
print("----------")

with open(newPathName) as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if row[0] != "Disc.":
            target.append(row[0])
            targSet.add(row[0])
            targWDSs.append(row[1])
            comps.append(row[2])
            obsTD.append(row[3])
            priRAs.append(row[4])
            priDecs.append(row[5])
            secRAs.append(row[6])
            secDecs.append(row[7])
            catPAs.append(row[8])
            catSeps.append(row[9])
            imagePAs.append(row[10])
            imageSeps.append(row[11])
            gaps.append(row[12])
            
uniqueTargs = list(targSet)
numUniqueTargs = len(uniqueTargs)

preSortFile = open(dirName + "temp_aligns.csv","w")

preSortFile.write("Disc.,Name,Comp.,Obs. T/D,P-RA (j2k),P-Dec (j2k),S-RA (j2k),S-Dec (j2k),Total Obs.,PA Vari.,Sep. Vari.," \
        + "Cat. PA,Cat. Sep.,PA,Sep.,PA Dif.,Sep. Dif.,Min. Gap" + CR)


#
# Process each unique target. As usual, not Pythonic but I hate inconsistancy
# in the way I handle arrays, I mean lists.
#
for index in range(len(uniqueTargs)):
    timeStamp("Processing " + str(index + 1) + " of " + str(numUniqueTargs) + " targets.")
    print("----------")

    writeNote("Observations:")
    print("")
    #
    # This builds a list of indexes for "duplicate" observations for the unique target
    # that we're currently processing.
    #
    repeats = [i for i, e in enumerate(target) if e == uniqueTargs[index] ]

    targSeps = []   # This will hold the separations for all of the observations
    targPAs = []    # Same idea for PAs
    compAngles = [] # This will hold the comparison angles between the target and zero to 
                    # determine if the observations are pointing the same way.
    goodObsTD = []                    
    goodPriRAs = []
    goodPriDecs = []
    goodSecRAs = []
    goodSecDecs = []
    goodGaps = []


    #
    # List off all the onbservations for the current target
    #
    for imageNumber in repeats:
        print("           " + target[imageNumber] + "\t" + imagePAs[imageNumber] + "\t" + imageSeps[imageNumber])

        #
        # If it's not a bad observation (couldn't plate solve, etc), record the values
        #
        if "X" not in imageSeps[imageNumber]:
            targSeps.append(float(imageSeps[imageNumber]))
            targPAs.append(float(imagePAs[imageNumber]))
            goodObsTD.append(str(obsTD[imageNumber]))
            goodPriRAs.append(float(priRAs[imageNumber]))
            goodPriDecs.append(float(priDecs[imageNumber]))
            goodSecRAs.append(float(secRAs[imageNumber]))
            goodSecDecs.append(float(secDecs[imageNumber]))
            goodGaps.append(float(gaps[imageNumber]))
            catPA = catPAs[imageNumber]                 # These should all be the same, just grab a valid one
            catSep = catSeps[imageNumber] 
            targWDS = targWDSs[imageNumber] 
            comp = comps[imageNumber]

    
    print("")
    #
    # This routine (coded above) will check the observations and then average them.
    #
    results = avgMeasures(targPAs, targSeps, goodPriRAs, goodPriDecs, goodSecRAs, goodSecDecs, goodGaps)    


    if comp:
    #
    # This cleans up the output in case I use a custom SDB that includes components as
    # part of the name.
    #
        if (comp in uniqueTargs[index]):
            uniqueTargs[index] = uniqueTargs[index].strip(comp)

    else:
    #
    # I do this because some of the binary systems don't specify AB
    # because it is assumed.
    #
        comp = "AB"

    #
    # This just cleans up the name for consistancy between catalogs
    #

    if ("WDS-2018" in uniqueTargs[index]):
        uniqueTargs[index] = uniqueTargs[index].replace("WDS-2018", "WDS")

    if ("WDS-2019-C" in uniqueTargs[index]):
        uniqueTargs[index] = uniqueTargs[index].replace("WDS-2019-C", "WDS")

    if ("WDS-2019" in uniqueTargs[index]):
        uniqueTargs[index] = uniqueTargs[index].replace("WDS-2019", "WDS")

    uniqueTargs[index] =  " ".join(uniqueTargs[index].split())

    if (results == "noPA"):
        badStars = badStars + 1
    else:
        avgPA, avgSep, observs, paFinalSD, sepFinalSD, priRA, priDec, secRA, secDec, avgGap = results.split("; ")

        avgTD = avgTDStamps(goodObsTD)

        avgPA = float(avgPA)
        avgSep = float(avgSep)
        observs = int(observs)
        paFinalSD = float(paFinalSD)
        sepFinalSD = float(sepFinalSD)
        priRA = round(float(priRA),6)
        priDec = round(float(priDec),5)
        secRA = round(float(secRA),6)
        secDec = round(float(secDec), 5)
        avgGap = round(float(avgGap), 2)
        
        if "NA" not in catPA:
            catPA = float(catPA)
        else:
            catPA = "X"
        
        if "NA" not in catSep:
            catSep = float(catSep)
        else:
            catSep = "X"
        
        avgSep = float(avgSep)

        print("----------")

        writeNote("Component: " + comp)
        writeNote("Used " + str(observs) + " observations.")
        print("----------")

        writeNote("Avg. UTC:\t" + avgTD)
        print("----------")


        writeNote("PA:\t" + str(avgPA))
        writeNote("Sep.:\t" + str(avgSep))
        print("")
        writeNote("Cat PA:\t" + str(catPA))
        writeNote("Cat Sep:\t" + str(catSep))

        print("")


        if ("X" in str(catPA)) or ("X" in str(catSep)):

            writeNote("No catalog values available for comparison.")
            status = "uncompared"

        else:

            sepDif = round(abs(catSep - avgSep),1) 
            PAdif = round(calcCircDif(avgPA, catPA), 1)


            preSortFile.write(uniqueTargs[index] + "," + str(targWDS) + "," + comp + "," + avgTD + "," + str(priRA) + "," + str(priDec) \
                + "," + str(secRA) + "," + str(secDec) \
                + "," + str(observs) + "," + str(paFinalSD) + "," + str(sepFinalSD) + "," + str(catPA) + "," + str(catSep) \
                + "," + str(avgPA) + "," + str(avgSep) + "," + str(PAdif) + "," + str(sepDif) + "," + str(avgGap) + CR)
            

preSortFile.close()

# Try to figure out what an acceptable variation range is for the 
# separation values. It uses a tiered approach. First tier knocks out
# the huge outliers and the second tier calculates variance based
# on the remainders. Any differences above that threshold will be
# considered unaligned with catalog expectations.


paDif = []
sepDif = []


with open(dirName + "temp_aligns.csv") as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        if "Disc." not in row[0]:
            paDif.append(float(row[14]))
            sepDif.append(float(row[15]))
            

print("----------")
timeStamp("Observation vs. Catalog Difference Distribution Statistics")
print("----------")

preSortMedian = round(statistics.median(sepDif), 2)
preSortSD = round(statistics.pstdev(sepDif), 2)

writeNote("First Stage Separation Difference Distribution")
writeNote(" Median: " + str(preSortMedian))
writeNote(" Standard Deviation: " + str(preSortSD))

firstSortPAMedian = round(statistics.median(paDif), 2)
firstSortPASD = round(statistics.pstdev(paDif), 2)

print("")

writeNote("First Stage Position Angle Difference Distribution")
writeNote(" Median: " + str(firstSortPAMedian))
writeNote(" Standard Deviation: " + str(firstSortPASD))

print("")

secondSortSepDifs = []
secondSortPADifs = []

for index in range(len(sepDif)):
    if sepDif[index] < preSortSD:
        secondSortSepDifs.append(sepDif[index])
        secondSortPADifs.append(paDif[index])


if (len(secondSortSepDifs)) > 3:
    secondSortMedian = round(statistics.median(secondSortSepDifs), 2)
    secondSortSD = round(statistics.pstdev(secondSortSepDifs), 2)

    secondSortPAMedian = round(statistics.median(secondSortPADifs), 2)
    secondSortPASD = round(statistics.pstdev(secondSortPADifs), 2)
    

    writeNote("Second Stage Separation Difference Distribution")
    writeNote(" Median: " + str(secondSortMedian))
    writeNote(" Standard Deviation: " + str(secondSortSD))
    print("")


    writeNote("Second Stage Position Angle Difference Distribution")
    writeNote(" Median: " + str(secondSortPAMedian))
    writeNote(" Standard Deviation: " + str(secondSortPASD))
    print("")





else:

    secondSortMedian = preSortMedian
    secondSortSD = preSortSD



print("----------")


#
# Sort the temp file
#
with open(dirName + "temp_aligns.csv") as reReadDataFile:
    unsortedDataStream = csv.reader(reReadDataFile, delimiter=',')
    RASortedData = sorted(unsortedDataStream, key=operator.itemgetter(1))

#
# Write the sorted data to the "final" aligned file
#
with open(dirName + "sortedByRA.csv", "w") as sortedFile:
    fileWriter = csv.writer(sortedFile, delimiter=',')
    for row in RASortedData:
        fileWriter.writerow(row)

if os.path.exists(dirName + "temp_aligns.csv"):
    os.remove(dirName + "temp_aligns.csv")


#
# Open up the final files
#

reliableCount = 0
notReliableCount = 0

missFile = open(dirName + "deviants.csv","w")
tightFile = open(dirName + "too_close.csv","w")
hitFile = open(dirName + "aligned.csv","w")

missFile.write("Disc.,Name,Comp.,Mid. Exp. (UTC),P-RA (j2k),P-Dec (j2k),S-RA (j2k),S-Dec (j2k),Obs.,PA SD,Sep. SD," \
        + "Cat. PA,Cat. Sep.,PA,Sep.,PA Dif. Sep. Dif." + CR)

tightFile.write("Disc.,Name,Comp.,Mid. Exp. (UTC),P-RA (j2k),P-Dec (j2k),S-RA (j2k),S-Dec (j2k),Obs.,PA SD,Sep. SD," \
        + "Cat. PA, Cat. Sep.,PA,Sep.,PA Dif.,Sep. Dif.,Res. Limit" + CR)

hitFile.write("Disc.,Name,Comp.,Mid. Exp. (UTC),P-RA (j2k),P-Dec (j2k),S-RA (j2k),S-Dec (j2k),Obs.,PA SD,Sep. SD," \
        + "Cat. PA,Cat. Sep.,PA,Sep.,PA Dif.,Sep. Dif." + CR)


with open(dirName + "sortedByRA.csv") as sortedDataFile:
    sortedDataStream = csv.reader(sortedDataFile, delimiter=',')
    for row in sortedDataStream:
        # This zero length weirdness is here to deal with odd Windows black row CR insertions)
        if ("Disc." not in row) and (len(row) > 0):

            avgSep = float(row[14])
            PAdif = float(row[15])
            sepDif = float(row[16])
            avgGap = float(row[17])

            if (PAdif <= firstSortPASD) and (sepDif <= secondSortSD ):
                status = "aligns"
            else:
                status = "deviates"
            
            if (avgGap > avgSep):
                reliability = "below"
            else:
                reliability = "above"

            if (reliability == "above") and (status == "aligns"):
                hitFile.write(row[0] + "," + row[1] + "," + row[2] + "," + row[3] + "," + row[4] + "," + row[5] + "," + row[6] + ","\
                        + row[7] + "," + row[8] + "," + row[9] + "," + row[10] + "," + row[11] + "," + row[12] + "," + row[13] + "," + \
                        row[14] + "," + row[15] + "," + row[16] + CR)

                reliableCount = reliableCount + 1

            elif (reliability == "above") and (status != "aligns"):
                missFile.write(row[0] + "," + row[1] + "," + row[2] + "," + row[3] + "," + row[4] + "," + row[5] + "," + row[6] + ","\
                        + row[7] + "," + row[8] + "," + row[9] + "," + row[10] + "," + row[11] + "," + row[12] + "," + row[13] + "," + \
                        row[14] + "," + row[15]  + "," + row[16] + CR)

                reliableCount = reliableCount + 1


            else:
                tightFile.write(row[0] + "," + row[1] + "," + row[2] + "," + row[3] + "," + row[4] + "," + row[5] + "," + row[6] + ","\
                        + row[7] + "," + row[8] + "," + row[9] + "," + row[10] + "," + row[11] + "," + row[12] + "," + row[13] + "," + \
                        row[14] + "," + row[15] + "," + row[16] + "," + str(avgGap) + CR)

                notReliableCount = notReliableCount + 1



hitFile.close()
missFile.close()
tightFile.close()

if os.path.exists(dirName + "sortedByRA.csv"):
    os.remove(dirName + "sortedByRA.csv")

timeStamp(str(reliableCount) + " stars were measured reliably.")
timeStamp(str(notReliableCount) + " stars were measured but not considered reliable due to resolution.")
timeStamp(str(badStars) + " stars could not be measured at all.")

