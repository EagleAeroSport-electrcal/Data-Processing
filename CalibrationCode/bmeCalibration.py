"""Convert raw values from a BME280 to SI units.

Each Function is passed the necessary calibration coefficents and a raw
value, and returns a compensated value.
individually.
"""
from typing import Tuple, Union, Optional
from numpy import uint32 as uint32_t
from numpy import uint64 as uint64_t
# TODO add some logging code?
# Predefine some of the constants
# TODO Double check how necessary this is
# TODO Finish adding constants (if needed)


TemperatureCoefsType = Tuple[int, int, int]
PressureCoefsType = Tuple[int, int, int, int, int, int, int, int, int]
HumidityCoefsType = Tuple[int, int, int, int, int, int]
CoefsType = Tuple[TemperatureCoefsType, PressureCoefsType, HumidityCoefsType]
ValsType = Tuple[int, int, int]


tempMin: uint32_t = uint32_t(-4000)
tempMax: uint32_t = uint32_t(8500)
pressureMin: uint32_t = uint32_t(3000000)
pressureMax: uint32_t = uint32_t(11000000)
humidityMax: uint32_t = uint32_t(100000)


# Raw Values and calibration coefficents
# This part calculats tFine and the actual temperature value
# Based off of line 1014 of the BME280 driver

class CompensateBME280:
    """Perform BME280 compensation using numpy integers."""

    def __init__(self, coefs: CoefsType, uTemp: int, uPres: int, uHumid: int) -> None:
        """Set up all of the variables."""
        self.temperature: int
        self.tFine: uint32_t
        self.temperature, self.tFine = self.compensateTemp(uTemp, coefs[0])
        self.pressure = self.compensatePres(uPres, coefs[1], self.tFine)
        self.humidity = self.compensateHumid(uHumid, coefs[2], self.tFine)

    @staticmethod
    def compensateTemp(uTemp: int, tCoefs: TemperatureCoefsType) -> Tuple[int, uint32_t]:
        """Convert raw temperature into a useable values.

        Args:
            uTemp: The uncompensated temperature value
            tCoefs: The calibration coefficents

        Returns:
            Tuple of the calibrated temperature, and the value of tFine

        """
        var1: uint32_t = uint32_t((uTemp / 8) - (tCoefs[0] * 2))
        var1 = uint32_t((var1 * tCoefs[1]) / 2048)

        var2: uint32_t = uint32_t((uTemp / 16) - (tCoefs[0]))
        var2 = uint32_t((((var2 * var2) / 4096) * (tCoefs[2])) / 16384)
        tFine = uint32_t(var1 + var2)
        temperature: uint32_t = uint32_t((tFine * 5 + 128) / 256)
        return int(temperature), tFine

    # This part calculates the actual pressure
    @staticmethod
    def compensatePres(uPres: int, pCoefs: PressureCoefsType, tFine: uint32_t) -> int:
        """Convert the raw pressure values into useable units.

        Args:
            uPres: Tee uncompensated Pressure Values
            pCoefs: Tuple of pressure compensation coefficents
            tFine: Fine temperature calculation from compensateTemp

        Returns:
            Integer of the calculated pressure

        """
        var1: uint64_t = uint64_t(tFine - 128000)
        var2: uint64_t = uint64_t(var1 * var1 * pCoefs[5])
        var2 = uint64_t(var2 + (var1 * pCoefs[4] * 131072))
        var2 = uint64_t(var2 + (pCoefs[3] * 34359738368))
        var1 = uint64_t((var1 * var1 * pCoefs[2] / 256) + (var1 * pCoefs[1] * 4096))
        var3: uint64_t = uint64_t(1 * 140737488355328)
        var1 = uint64_t((var3 + var1) * (pCoefs[0] / 8589934592))
        # Avoids a divide by zero exception for pressure
        if var1:
            var4: uint64_t = uint64_t(1048576 - uPres)
            # FIXME Does this need int64_t calling?
            var4 = uint64_t((((var4 * 2147483648) - var2) * 3125) / var1)
            var1 = uint64_t((pCoefs[8]) * (var4 / 8192) * (var4 / 8192)) / 33554432
            var2 = uint64_t((pCoefs[7] * var4) / 524288)
            var4 = uint64_t((var4 + var1 + var2) / 256 + ((pCoefs[6] * 16)))
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
    def compensateHumid(uHumid: int, hCoefs: HumidityCoefsType, tFine: Union[float, int]) -> int:
        """Compensates the raw humidity values, making it user readable.

        Args:
            uHumid: The uncompensated humidity value
            hCoefs: Tuple with the compensation coefficents
            tFine: Fine temperature value from compensateTemp

        Returns: Compensated humidity value

        """
        var1: uint32_t = uint32_t(tFine - 76800)
        var2: uint32_t = uint32_t(uHumid * 16384)
        var3: uint32_t = uint32_t(hCoefs[3] * 1048576)
        var4: uint32_t = uint32_t(hCoefs[4] * var1)
        var5: uint32_t = uint32_t((((var2 - var3) - var4) + 16384) / 32768)
        var2 = uint32_t(var1 * (hCoefs[5] / 32768))
        var3 = uint32_t((var1 * (hCoefs[2] / 2048)))
        var4 = uint32_t((var2 * (var3 + 32768) / 1024) + 2097152)
        var2 = uint32_t(((var4 * (hCoefs[1])) + 8192) / 16384)
        var3 = uint32_t(var5 * var2)
        var4 = uint32_t(((var3 / 32768) * (var3 / 32768)) / 128)
        var5 = uint32_t(var3 - ((var4 * hCoefs[0]) / 16))
        if var5 < 0:
            var5 = uint32_t(0)
        elif var5 > 419430400:
            var5 = uint32_t(419430400)

        humidity = uint32_t(var5 / 4096)
        if humidity > humidityMax:
            humidity = humidityMax
        return int(humidity)


class CompensateBME280Native:
    """Perform BME280 compensation using python native int and float."""

    def __init__(self, coefs: CoefsType, uTemp: int, uPres: int, uHumid: int) -> None:
        """Initialize Instance."""
        self.tCoefs: TemperatureCoefsType = coefs[0]
        self.pCoefs: PressureCoefsType = coefs[1]
        self.hCoefs: HumidityCoefsType = coefs[2]
        self.uTemp: int = uTemp
        self.uPres: int = uPres
        self.uHumid: int = uHumid
        self.tFine: uint32_t = self.compensateTemp(self.uTemp, self.tCoefs)[1]

    def compensateAll(self, coefs: Optional[CoefsType] = None, uncompVals: Optional[ValsType] = None) -> ValsType:
        """Calculate all compensation values for the bme 280."""
        temperature: int
        tFine: uint32_t
        pressure: int
        humidity: int

        if coefs is not None and uncompVals is not None:
            temperature, tFine = self.compensateTemp(uncompVals[0], coefs[0])
            pressure = self.compensatePres(uncompVals[1], coefs[1], tFine)
            humidity = self.compensateHumid(uncompVals[2], coefs[2], tFine)
        else:
            temperature, tFine = self.compensateTemp(self.uTemp, self.tCoefs)
            pressure = self.compensatePres(self.uPres, self.pCoefs, tFine)
            humidity = self.compensateHumid(self.uHumid, self.hCoefs, tFine)
        return(temperature, pressure, humidity)

    def compensateTemp(self, uTemp: int, tCoefs: TemperatureCoefsType,) -> Tuple[int, Union[int, float]]:
        """Convert raw temperature into a useable values."""
        if uTemp is None or tCoefs is None:
            uTemp = self.uTemp
            tCoefs = self.tCoefs
            tFine = self.tFine

        var1: uint32_t = (uTemp / 8) - (tCoefs[0] * 2)
        var1 = (var1 * tCoefs[1]) / 2048

        var2: uint32_t = (uTemp / 16) - (tCoefs[0])
        var2 = (((var2 * var2) / 4096) * (tCoefs[2])) / 16384
        tFine = var1 + var2
        temperature: uint32_t = (tFine * 5 + 128) / 256
        return temperature, tFine

    def compensatePres(self, uPres: int, pCoefs: PressureCoefsType, tFine: uint32_t) -> int:
        """Convert the raw pressure values into useable units."""
        if uPres is None or pCoefs is None:
            uPres = self.uPres
            pCoefs = self.pCoefs
            tFine = self.tFine
        var1: uint64_t = tFine - 128000
        var2: uint64_t = var1 * var1 * pCoefs[5]
        var2 = var2 + (var1 * pCoefs[4] * 131072)
        var2 = var2 + (pCoefs[3] * 34359738368)
        var1 = (var1 * var1 * pCoefs[2] / 256) + (var1 * pCoefs[1] * 4096)
        var3: uint64_t = 1 * 140737488355328
        var1 = (var3 + var1) * (pCoefs[0] / 8589934592)
        # Avoids a divide by zero exception for pressure
        if var1:
            var4: uint64_t = 1048576 - uPres
            # FIXME Does this need int64_t calling?
            var4 = (((var4 * 2147483648) - var2) * 3125) / var1
            var1 = (pCoefs[8]) * (var4 / 8192) * (var4 / 8192) / 33554432
            var2 = (pCoefs[7] * var4) / 524288
            var4 = (var4 + var1 + var2) / 256 + ((pCoefs[6] * 16))
            pressure: uint32_t = ((var4 / 2) * 100) / 128

            # Compensate for risks of exceedig min and max pressure
            if pressure < pressureMin:
                pressure = pressureMin
            elif pressure > pressureMax:
                pressure = pressureMax
        else:
            pressure = pressureMin
        return int(pressure)

    def compensateHumid(self, uHumid: int, hCoefs: HumidityCoefsType, tFine: Union[float, int]) -> int:
        """Compensates the raw humidity values, making it user readable."""
        if uHumid is None or hCoefs is None:
            uHumid = self.uHumid
            hCoefs = self.hCoefs
            tFine = self.tFine
        var1: uint32_t = tFine - 76800
        var2: uint32_t = uHumid * 16384
        var3: uint32_t = hCoefs[3] * 1048576
        var4: uint32_t = hCoefs[4] * var1
        var5: uint32_t = (((var2 - var3) - var4) + 16384) / 32768
        var2 = var1 * (hCoefs[5] / 32768)
        var3 = (var1 * (hCoefs[2] / 2048))
        var4 = (var2 * (var3 + 32768) / 1024) + 2097152
        var2 = ((var4 * (hCoefs[1])) + 8192) / 16384
        var3 = var5 * var2
        var4 = ((var3 / 32768) * (var3 / 32768)) / 128
        var5 = var3 - ((var4 * hCoefs[0]) / 16)
        if var5 < 0:
            var5 = 0
        elif var5 > 419430400:
            var5 = 419430400

        humidity = var5 / 4096
        if humidity > humidityMax:
            humidity = humidityMax
        return int(humidity)
