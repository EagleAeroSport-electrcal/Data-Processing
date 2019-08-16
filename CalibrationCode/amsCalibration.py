#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calculate useable temperature and pressure values from the AMS5915."""

# TODO Look into necessary variable types using numpy


def calibrateTemp(rawTemp):
    """Get calibrated temperature from raw temp."""
    return ((rawTemp * 200) / 2048) - 50


def calibratePressure(rawPressure, digiOutPMin, digiOutPMax, pMin, pMax):
    """Get calibrated pressure from raw pressure."""
    sensep = (digiOutPMax - digiOutPMin) / (pMax - pMin)
    return ((rawPressure - digiOutPMin) / (sensep)) + pMin
