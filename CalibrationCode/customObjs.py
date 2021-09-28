#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom Objects for the module."""
from dataclasses import dataclass

from numpy import int32, int64

from CalibrationCode.typeAliases import (HumidityCoefsType, PresCoefsType,
                                         TempCoefsType)


@dataclass
class BME280Coefficents:
    """Named Tuple for holding calibration coefficents for a sensor."""

    temperature: TempCoefsType
    pressure: PresCoefsType
    humidity: HumidityCoefsType
    ID: int


@dataclass
class _BME280TemperatureCoefficents():
    """Named Tuple for all of the temperatre calibration coefficents on the BME280."""

    T1: int
    T2: int
    T3: int

    def toInt32(self):
        """Convert attributes in dataclass to numpy int32 objects."""
        self.T2 = int32(self.T2)    # pylint: disable=invalid-name
        self.T3 = int32(self.T3)    # pylint: disable=invalid-name
        self.T1 = int32(self.T1)    # pylint: disable=invalid-name


@dataclass
class _BME280PressureCoefficents():
    P1: int
    P2: int
    P3: int
    P4: int
    P5: int
    P6: int
    P7: int
    P8: int
    P9: int

    def toInt64(self):
        self.P1 = int64(self.P1)    # pylint: disable=invalid-name
        self.P2 = int64(self.P2)    # pylint: disable=invalid-name
        self.P3 = int64(self.P3)    # pylint: disable=invalid-name
        self.P4 = int64(self.P4)    # pylint: disable=invalid-name
        self.P5 = int64(self.P5)    # pylint: disable=invalid-name
        self.P6 = int64(self.P6)    # pylint: disable=invalid-name
        self.P7 = int64(self.P7)    # pylint: disable=invalid-name
        self.P8 = int64(self.P8)    # pylint: disable=invalid-name
        self.P9 = int64(self.P9)    # pylint: disable=invalid-name


class _BME280HumidityCoefficents():
    H1: int
    H2: int
    H3: int
    H4: int
    H5: int
    H6: int

    def toInt32(self):
        self.H1 = int32(self.H1)    # pylint: disable=invalid-name
        self.H2 = int32(self.H2)    # pylint: disable=invalid-name
        self.H3 = int32(self.H3)    # pylint: disable=invalid-name
        self.H4 = int32(self.H4)    # pylint: disable=invalid-name
        self.H5 = int32(self.H5)    # pylint: disable=invalid-name
        self.H6 = int32(self.H6)    # pylint: disable=invalid-name
