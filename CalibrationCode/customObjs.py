#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom Objects for the module."""
from typing import NamedTuple
from CalibrationCode.typeAliases import TempCoefsType, PresCoefsType, HumidityCoefsType


class BME280Coefficents(NamedTuple):
    """Named Tuple for holding calibration coefficents for a sensor."""

    temperature: TempCoefsType
    pressure: PresCoefsType
    humidity: HumidityCoefsType
    ID: int
