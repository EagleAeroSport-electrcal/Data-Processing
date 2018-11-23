"""
This is the top level file for the EAS Data extraction module.

It reads the calibration coefficents and the raw data from the EAS Log files,
organizes them, and calculates SI values for each raw data point, saving it as
in a form for other scripts to acces and operate on (such as saving to a file,
or graphing).
"""

# Disable alert about improper case of variable. I prefer camelcase
# pylint: disable-msg=C0103

# pylint gets confused about indentation, just disable the warning.
# pylint: disable-msg=C0330


# Nesting in try blocks to see if the code is being run from a system with top
# level as github repo


try:
    f = open('easRV12_15_Nov_2018_21_15_33.log', 'rb')
except FileNotFoundError:
    f = open('CalibrationCode\easRV12_15_Nov_2018_21_15_33.log', 'rb')


# Each DAQpack is 24 bytes long

# Reads the entire text file
data = f.read()

# Split the file up into the header and raw data.
# THIS needs tweaking, some log files will have a larger header,
# but data always begins at a multilpe of 0x400
header = data[:0x400]
rawData = data[0x400:]

splitData = []
brokenDown = []
compHumid = []

# Convert header to string
header = header.decode("utf-8")

header = header.split('-----')
presCalibrations = {}


def coefS16(string, points):
    """Get a signed 16-bit value from the provided string."""
    result = coefU(string, points)
    if result > 32767:
        result -= 65536
    return result


def coefU(string, points):
    """Get an unsigned ing from the provided string."""
    return int(''.join([string[i] for i in points]), 16)


def coefS8(string, points):
    """Get a signed 8-bit value from the provided string."""
    result = coefU(string, points)
    if result > 127:
        result -= 256
    return result


for i, value in enumerate(header):
    header[i] = header[i].splitlines()
    header[i][:] = [item for item in header[i] if item]

    # This part might not be necessary once we get the beginning of the raw
    # data down cold
    if "\x00\x00\x00" in header[i][0]:
        del header[i]

    elif "BME280 Temperature Humidity Pressure Sensor" in header[i][1]:
        sensorID = int(header[i][0].split(': ')[1])
        # This part is just for debugging at the moment. It lists BME280s
        # print("Found a pressure sensor at index " + str(i))

        # Initialize a new entry in the dictionary of calibrations.
        presCalibrations[sensorID] = {}

        # Parse the calibration line to be only the characters that we want
        calString = (header[i][5].split('||')[1])

        # Calculate the temperature calibration values
        presCalibrations[sensorID]['temperature'] = [
            coefU(calString, [2, 3, 0, 1]),
            coefS16(calString, [6, 7, 4, 5]),
            coefS16(calString, [10, 11, 8, 9])
        ]

        # Calculate the Pressure calibration values
        presCalibrations[sensorID]['pressure'] = [
            coefU(calString, [14, 15, 12, 13]),
            coefS16(calString, [18, 19, 16, 17]),
            coefS16(calString, [22, 23, 20, 21]),
            coefS16(calString, [26, 27, 24, 25]),
            coefS16(calString, [31, 30, 28, 29]),
            coefS16(calString, [34, 35, 32, 33]),
            coefS16(calString, [38, 39, 36, 37]),
            coefS16(calString, [42, 43, 40, 41]),
            coefS16(calString, [46, 47, 44, 45])
        ]

        # Calculate the humidity calibrations values
        presCalibrations[sensorID]['humidity'] = [
            coefU(calString, [48, 49]),
            coefS16(calString, [52, 53, 50, 51]),
            coefU(calString, [54, 55]),
            # These variables here are weird, because of
            # how they are set up
            # (h4 and h5 share some data in registers)

            # This way of doing it is copied from
            # adafruit's library, lines 166 through 173
            ((coefS8(calString, [56, 57]) << 4) \
             | (coefU(calString, [58, 59]) & 0x0F)),

            (coefS8(calString, [60, 61]) << 4 \
             | (coefU(calString, [58, 59]) >> 4 & 0x0F)),

            coefS8(calString, [62, 63])]

# Seperate the Raw data into each packet
# This seems to cut off the last data section right now
for i in range(0, int(len(rawData) / 24)):
    splitData.append(rawData[24*i:24*i+24])

# Split the information in each packet into the proper type
uCompData = [{}] * len(splitData)
for i, val in enumerate(splitData):
    packetType = int.from_bytes(splitData[i][4:8], byteorder='little')
    if packetType == 0:
        # Undef, Means something weird happened and we need to check CPP
        # code for errors
        pass
    elif packetType == 0x01:
        pass
        # Timestamp packet. Talk to Dr. Davis
    elif packetType == 0x02:
        # This is for the Acclerometer. Currently uses signed short 16,
        # so we need to be careful about this one
        uCompData[i] = {'ID': int.from_bytes(splitData[i][0:4],
                                             byteorder='little'),
                        'type': packetType,
                        'uAccX': int.from_bytes(splitData[i][8:10],
                                                byteorder='little'),
                        'uAccY': int.from_bytes(splitData[i][10:12],
                                                byteorder='little'),
                        'uAccZ': int.from_bytes(splitData[i][12:14],
                                                byteorder='little')}

    elif packetType == 0x03:
        # Barotemp type packet. Used with the BMP180
        uCompData[i] = {'ID': splitData[i][0],
                        'type': packetType,
                        'uPres': int.from_bytes(splitData[i][8:12],
                                                byteorder='little'),
                        'uTemp': int.from_bytes(splitData[i][12:14],
                                                byteorder='little'),
                        }
    elif packetType == 0x04:
        # Gyro Type Sensor. unused in code (commit  182fe0c)
        pass
    elif packetType == 0x05:
        # Strain Gauge. CUrrently unused in code (commit  182fe0c)
        pass
    elif packetType == 0x06:
        # CLOCK_T Unknown use
        pass
    elif packetType == 0x07:
        # MPU6050_t
        uCompData[i] = {'ID': int.from_bytes(splitData[i][0:4],
                                             byteorder='little'),
                        'type': packetType,
                        'uAccX': int.from_bytes(splitData[i][8:10],
                                                byteorder='little'),
                        'uAccY': int.from_bytes(splitData[i][10:12],
                                                byteorder='little'),
                        'uAcczZ': int.from_bytes(splitData[i][12:14],
                                                 byteorder='little'),
                        'uGyroX': int.from_bytes(splitData[i][14:16],
                                                 byteorder='little'),
                        'uGyroY': int.from_bytes(splitData[i][16:18],
                                                 byteorder='little'),
                        'uGyroZ': int.from_bytes(splitData[i][18:20],
                                                 byteorder='little'),
                        'uTemp': int.from_bytes(splitData[i][20:22],
                                                byteorder='little'),
                        }
    elif packetType == 0x08:
        # ADXL345_t currently unused in code (commit 182fe0c)
        pass
    elif packetType == 0x09:
        # BMP180_t currently unused (commit  182fe0c)
        pass
    elif packetType == 0x0a:
        # Prestemphuhid type packet. Used by BME280
        uCompData[i] = {'ID': int.from_bytes(splitData[i][0:4],
                                             byteorder='little'),
                        'type': packetType,
                        'uPres': int.from_bytes(splitData[i][8:12],
                                                byteorder='little'),
                        'uTemp': int.from_bytes(splitData[i][12:16],
                                                byteorder='little'),
                        'uHumid': int.from_bytes(splitData[i][16:18],
                                                 byteorder='little')
                        }

    elif packetType == 0x0b:
        # HSCpress packet. Used by our relative pressure sensors (pitot tubes)

        # Currently has some issues with the status bit, waiting on Dr. Davis
        # For a solution

        uCompData[i] = {'ID': splitData[i][0],
                        'type': packetType,
                        # 'status': int.from_bytes(bytessplitData[i][])
                        # 'uPres': int.
                        }
    elif packetType == 0x0c:
        # DUAL_Clock_t unknown use
        pass
    elif packetType == 0x0d:
        pass


# Packet Format is 1 byte ID for sensor, then a 4 byte ID for the packet type
# The rest of the bytes (19 of them) hold the data. The format for this changes
# Per sensor type. See eas_daq_pack.h in github repo for more info.

# print(item for item in uCompData if (item['ID'] == 2))

for item in range(0, 20):
    try:
        if uCompData[item]['ID'] == 2:
            print(uCompData[item])
    except:
        pass
