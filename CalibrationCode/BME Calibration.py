try:
    import numpy as np
    # TODO add some logging code?

    # Predefine some of the constants
    # TODO Double check how necessary this is
    # TODO Finish adding constants (if needed)

    tvar1 = np.int32()
    tvar2 = np.int32()
    temperature = np.int32()
    temperature_min = np.int32(-4000)
    temperature_max = np.int32(8500)
    pressure_min = np.int32(3000000)
    pressure_max = np.int32(11000000)
    humidity_max = np.int32(100000)

    # Raw Values and calibration coefficents
    # TODO add a way to read the log file. Need a file from someone else
    t1 = 1
    uTemp = 5

    # This part calculats t_fine and the actual temperature value
    # Based off of line 1014 of the BME280 driver
    def compensateTemp(uTemp, tCoefs):
        t1, t2, t3 = tCoefs

        global t_fine
        var1 = np.int32((uTemp / 8) - (t1 * 2))
        var1 = np.int32((var1 * t2) / 2048)

        var2 = np.int32((uTemp / 16) - (t1))
        var2 = np.int32((((var2 * var2) / 4096) * (t3)) / 16384)
        tFine = np.int32(var1 + var2)
        temperature = np.int32((tFine * 5 + 128) / 256)

    # This part calculates the actual pressure
    def compensatePres(uPres, pCoefs):
        p1, p2, p3, p4, p5, p6, p7, p8, p9 = pCoefs
        var1 = np.int64(tFine - 128000)
        var2 = np.int64(var1 * var1 * p6)
        var2 = np.int64(var2 + (var1 * p5 * 131072))
        var2 = np.int64(var2 + (P4 * 34359738368))
        var1 = np.int64((var1 * var1 * p3 / 256) + (var1 * p2 * 4096))
        var3 = np.int64(1 * 140737488355328)        # TODO DOUBLE CHECK THIS
        var1 = np.int64((var3 + var1) * (p1 / 8589934592))
        # Avoids a divide by zero exception for pressure
        if(var1 != 0):
            var4 = np.int64(1048576 - uPres)
            # Does this need np.int64 calling?
            var4 = np.int64((((var4 * 2147483648) - var2) * 3125) / var1)
            var1 = np.int64((p9) * (var4 / 8192) * (var4 / 8192)) / 33554432
            var2 = np.int64((p8 * var4) / 524288)
            var4 = np.int64((var4 + var1 + var2) / 256 + ((p7 * 16)))
            pressure = np.int32(((var4 / 2) * 100) / 128)

            # Compensate for risks of exceedig min and max pressure
            if (pressure < pressure_min):
                pressure = pressure_min
            elif(pressure > pressure_max):
                pressure = pressure_max
        else:
            pressure = pressure_min

# This part compensates the humindity.
    def compensateHumid(uHUmid, hCoefs):
        h1, h2, h3, h4, h5, h6 = hCoefs
        var1 = np.int32(tFine - 76800)
        var2 = np.int32(uHUmid * 16384)
        var3 = np.int32(h4 * 1048576)
        var4 = np.int32(h5 * var1)
        var5 = np.int32((((var2 - var3) - var4) + 16384) / 32768)
        var2 = np.int32(var1 * (h6 / 32768))
        var3 = np.int32((var1 * (h3 / 2048)))
        var4 = np.int32((var2 * (var3 + 32768) / 1024) + 2097152)
        var2 = np.int32(((var4 * (h2)) + 8192) / 16384)
        var3 = np.int32(var5 * var2)
        var4 = np.int32(((var3 / 32768) * (var3 / 32768)) / 128)
        var5 = np.int32(var3 - ((var4 * h1) / 16))
        if(var5 < 0):
            var5 = 0
        else:
            var5 = var5
        if(var5 > 419430400):
            var5 = 419430400
        else:
            var5 = var5

        humidity = np.in32(var5 / 4096)
        if(humidity > humidity_max):
            humidity = humidity_max


# For future use in logging errors, Currently would do nothing
except ModuleNotFoundError as error:
    raise