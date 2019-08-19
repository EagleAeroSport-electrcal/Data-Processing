#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert raw values from a BME280 to SI units.

Each Function is passed the necessary calibration coefficents and a raw
value, and returns a compensated value.
individually.
"""
from typing import Tuple, Union
from numpy import uint32 as uint32_t
from numpy import int32 as int32_t
from numpy import int64 as int64_t
from CalibrationCode.customObjs import BME280Coefficents
from CalibrationCode.typeAliases import TempCoefsType, PresCoefsType, HumidityCoefsType
# TODO add some logging code?
# Predefine some of the constants
# TODO Finish adding constants (if needed)


class CompensateBME280:
    """Perform BME280 compensation using numpy integers.

    Args:
        coefs (CoefsType): The Calibration Coefficents for the BME 280 as a dictionary containing elements
            temperature, pressure, and humidity, each of which contains a list of the calibration coefficents.
        uTemp (int): The uncompensated temperature value.
        uPres (int): The uncompensated pressure value.
        uHumid (int): The uncompensated humidity value.

    Attributes
        temperature (int): The compensated temperature value.
        tFine (uint32_t): The fine temperature value, used for compensating pressure and humidity.
        pressure (int): The compensated pressure value.
        humidity (int): The compensated humidity.

    """

    def __init__(self, coefs: BME280Coefficents, uTemp: int, uPres: int, uHumid: int) -> None:
        """Initialize an object containing compensated values for the BME280."""    # noqa: I101
        self.temperature: int
        self.tFine: uint32_t
        self.temperature, self.tFine = self.compensateTemp(uTemp, coefs.temperature)
        self.pressure = self.compensatePres(uPres, coefs.pressure, self.tFine)
        self.humidity = self.compensateHumid(uHumid, coefs.humidity, self.tFine)

    @staticmethod
    def compensateTemp(uTemp: int, tCoefs: TempCoefsType) -> Tuple[int, int32_t]:
        """Convert raw temperature into a useable values.

        Args:
            uTemp: The uncompensated temperature value
            tCoefs: The calibration coefficents

        Returns:
            Tuple of the calibrated temperature, and the value of tFine

        """
        # Derived from Bosch BME280 driver, line 1121
        tempMin = -4000
        tempMax = 8500
        # Raw Values and calibration coefficents
        # This part calculats tFine and the actual temperature value
        # Based off of line 1014 of the BME280 driver
        var1: int32_t = int32_t((uTemp // 8) - (tCoefs[0] * 2))
        var1 = (var1 * int32_t(tCoefs[1])) // 2048

        var2: int32_t = int32_t((uTemp // 16) - (int32_t(tCoefs[0])))
        var2 = (((var2 * var2) // 4096) * int32_t(tCoefs[2])) // 16384
        tFine = var1 + var2
        temperature: int32_t = int32_t((tFine * 5 + 128) // 256)
        if temperature > tempMax:
            temperature = tempMax
        elif temperature < tempMin:
            temperature = tempMin
        return int(temperature), tFine

    # This part calculates the actual pressure
    @staticmethod
    def compensatePres(uPres: int, pCoefs: PresCoefsType, tFine: uint32_t) -> int:
        """Convert the raw pressure values into useable units.

        Args:
            uPres: The uncompensated Pressure Values
            pCoefs: Tuple of pressure compensation coefficents
            tFine: Fine temperature calculation from compensateTemp

        Returns:
            Integer of the calculated pressure

        """
        # Derived from bosch BME280 driver line 1154
        pressureMin = 3000000
        pressureMax = 11000000
        var1: int64_t = int64_t(tFine) - 128000
        var2: int64_t = var1 * var1 * int64_t(pCoefs[5])
        var2 = var2 + ((var1 * int64_t(pCoefs[4])) * 131072)
        var2 = var2 + (int64_t(pCoefs[3]) * 34359738368)
        var1 = ((var1 * var1 * int64_t(pCoefs[2])) / 256) + (var1 * int64_t(pCoefs[1]) * 4096)
        var3: int64_t = int64_t(1) * 140737488355328
        var1 = (var3 + var1) * (int64_t(pCoefs[0]) / 8589934592)
        # Avoids a divide by zero exception for pressure
        if var1:
            var4: int64_t = int64_t(1048576 - uPres)
            # FIXME Make sure int64_C is compatible with int64_t
            var4 = (((var4 * int64_t(2147483648)) - var2) * 3125) / var1
            var1 = (int64_t(pCoefs[8]) * (var4 / 8192) * (var4 / 8192)) / 33554432
            var2 = (int64_t(pCoefs[7]) * var4) / 524288
            var4 = ((var4 + var1 + var2) / 256) + (int64_t(pCoefs[6]) * 16)
            pressure: uint32_t = uint32_t(((var4 / 2) * 100) / 128)

            # Compensate for risks of exceedig min and max pressure
            if pressure < pressureMin:
                pressure = pressureMin
            elif pressure > pressureMax:
                pressure = pressureMax
        else:
            pressure = pressureMin
        return int(pressure)

    # This part compensates the humindity.
    @staticmethod
    def compensateHumid(uHumid: int, hCoefs: HumidityCoefsType, tFine: int32_t) -> int:
        """Compensates the raw humidity values, making it user readable.

        Args:
            uHumid: The uncompensated humidity value
            hCoefs: Tuple with the compensation coefficents
            tFine: Fine temperature value from compensateTemp

        Returns:
            Compensated humidity value

        """
        # Derived from bosch BME280 Driver line 1263
        humidityMax = uint32_t(102400)
        var1: int32_t = int32_t(tFine - 76800)
        var2: int32_t = int32_t(uHumid * 16384)
        var3: int32_t = int32_t(int32_t(hCoefs[3]) * 1048576)
        var4: int32_t = int32_t(hCoefs[4]) * var1
        var5: int32_t = (((var2 - var3) - var4) + 16384) / 32768
        var2 = (var1 * int32_t(hCoefs[5])) / 1024
        var3 = (var1 * int32_t(hCoefs[2])) / 2048
        var4 = ((var2 * (var3 + 32768)) / 1024) + 2097152
        var2 = ((var4 * (int32_t(hCoefs[1]))) + 8192) / 16384
        var3 = var5 * var2
        var4 = ((var3 / 32768) * (var3 / 32768)) / 128
        var5 = var3 - ((var4 * int32_t(hCoefs[0])) / 16)
        if var5 < 0:
            var5 = int32_t(0)
        elif var5 > 419430400:
            var5 = int32_t(419430400)

        humidity: uint32_t = uint32_t(var5 / 4096)
        if humidity > humidityMax:
            humidity = humidityMax
        return int(humidity)


class CompensateBME280Native:
    """Perform BME280 compensation using python native int and float.

    Args:
        coefs (CoefsType): The Calibration Coefficents for the BME 280 as a dictionary containing elements
            temperature, pressure, and humidity, each of which contains a list of the calibration coefficents.
        uTemp (int): The uncompensated temperature value.
        uPres (int): The uncompensated pressure value.
        uHumid (int): The uncompensated humidity value.

    Attributes
        temperature (int): The compensated temperature value.
        tFine (uint32_t): The fine temperature value, used for compensating pressure and humidity.
        pressure (int): The compensated pressure value.
        humidity (int): The compensated humidity.

    """

    def __init__(self, coefs: BME280Coefficents, uTemp: int, uPres: int, uHumid: int) -> None:
        """Initialize Instance."""  # noqa: I101
        self.temperature: float
        self.tFine: uint32_t
        self.temperature, self.tFine = self.compensateTemp(uTemp, coefs.temperature)
        self.pressure = self.compensatePres(uPres, coefs.pressure, self.tFine)
        self.humidity = self.compensateHumid(uHumid, coefs.humidity, self.tFine)

    @staticmethod
    def compensateTemp(uTemp: int, tCoefs: TempCoefsType) -> Tuple[float, float]:
        """Convert raw temperature into a useable values.

        Args:
            uTemp: The uncompensated temperature value
            tCoefs: The calibration coefficents

        Returns:
            Tuple of the calibrated temperature, and the value of tFine

        """
        # Derived from bosch BME280 Driver line 1005
        # Double Checked against Adafruit Python BME280 line 212
        tempMin = -40
        tempMax = 85
        var1: float = (uTemp) / 16384 - (tCoefs[0]) / 1024
        var1 = var1 * tCoefs[1]

        var2: float = uTemp / 131072 - tCoefs[0] / 8192
        var2 = (var2 * var2) * tCoefs[2]
        tFine = int(var1 + var2)
        temperature: float = (var1 + var2) / 5120
        if temperature < tempMin:
            temperature = tempMin
        elif temperature > tempMax:
            temperature = tempMax
        return temperature, tFine

    @staticmethod
    def compensatePres(uPres: int, pCoefs: PresCoefsType, tFine: int) -> float:
        """Convert the raw pressure values into useable units.

        Args:
            uPres: The uncompensated Pressure Values
            pCoefs: Tuple of pressure compensation coefficents
            tFine: Fine temperature calculation from compensateTemp

        Returns:
            Integer of the calculated pressure

        """
        pressureMin = 30000
        pressureMax = 110000
        # Derived from line 1035 of BME280 Bosch Driver
        # Double Checked against Adafruit Python BME280 line 223
        var1: float = (tFine / 2) - 64000
        var2: float = var1 * var1 * pCoefs[5] / 32768
        var2 = var2 + var1 * pCoefs[4] * 2
        var2 = (var2 / 4) + (pCoefs[3] * 65536)
        var3: float = pCoefs[2] * var1 * var1 / 524288
        var1 = (var3 + pCoefs[1] + var1) / 524288
        var1 = (1 + var1 + 32768) * pCoefs[0]
        # Avoids a divide by zero exception for pressure
        if var1:
            pressure: float = 1048576 - uPres
            pressure = (pressure - (var2 / 4096)) * 6250 / var1
            var1 = (pCoefs[8]) * pressure * pressure / 2147483648
            var2 = pressure * pCoefs[7] / 32768
            pressure = pressure + (var1 + var2 + pCoefs[6]) / 16

            # Compensate for risks of exceedig min and max pressure
            if pressure < pressureMin:
                pressure = pressureMin
            elif pressure > pressureMax:
                pressure = pressureMax
        else:
            pressure = pressureMin
        return pressure

    @staticmethod
    def compensateHumid(uHumid: int, hCoefs: HumidityCoefsType, tFine: Union[float, int]) -> float:
        """Compensates the raw humidity values, making it user readable.

        Args:
            uHumid: The uncompensated humidity value
            hCoefs: Tuple with the compensation coefficents
            tFine: Fine temperature value from compensateTemp

        Returns:
            Compensated humidity value

        """
        # Derived from Bosch BME280 Driver line 1082
        humidityMax = 100
        humidityMin = 0
        var1: float = tFine - 76800
        var2: float = hCoefs[3] * 64 * (hCoefs[4] / 16384.0 * var1)
        var3: float = uHumid - var2
        var4: float = hCoefs[1] / 65536
        var5: float = (1 + ((hCoefs[2]) / 67108864) * var1)
        var6: float = 1 + ((hCoefs[5]) / 67108864) * var1 * var5
        var6 = var3 * var4 * (var5 * var6)
        humidity: float = var6 * (1.0 - hCoefs[0] * var6 / 524288)
        if humidity > humidityMax:
            humidity = humidityMax
        elif humidity < humidityMin:
            humidity = humidityMin
        return humidity
