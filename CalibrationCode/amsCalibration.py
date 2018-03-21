#TODO Look into necessary variable types using numpy

def calibrateTemp(rawTemp):
    return ((rawTemp * 200) / 2048) - 50

def calibratePressure(rawPressure, digiOutPMin, sensp, pMin):
    return ((rawPressure - digiOutPMin) / ((digiOutPMax - digiOutPMin)/(pMin - pMax))) + pMin
