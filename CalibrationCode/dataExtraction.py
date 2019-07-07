"""This is the top level file for the EAS Data extraction module.

It reads the calibration coefficents and the raw data from the EAS Log files,
organizes them, and calculates SI values for each raw data point, saving it as
in a form for other scripts to acces and operate on (such as saving to a file,
or graphing).
"""
from typing import BinaryIO, List, Dict, Union


# Type hint aliases
PresCalType = Dict[Union[str, int], Dict[str, List[float]]]
UCompDataType = List[Dict[str, Union[int]]]


def coefS16(string, locations):
    """Get a signed 16-bit value from the provided string."""
    result = coefU(string, locations)
    if result > 32767:
        result -= 65536
    return result


def coefU(string, locations):
    """Get an unsigned int from the provided string."""
    return int(''.join([string[element] for element in locations]), 16)


def coefS8(string, locations):
    """Get a signed 8-bit value from the provided string."""
    result = coefU(string, locations)
    if result > 127:
        result -= 256
    return result


# Nesting in try blocks to see if the code is being run from a system with top
# level as github repo

data: bytes
f: BinaryIO
try:
    with open('easRV12_15_Nov_2018_21_15_33.log', 'rb') as f:
        data = f.read()
except FileNotFoundError:
    with open('CalibrationCode\\easRV12_15_Nov_2018_21_15_33.log', 'rb') as f:
        data = f.read()


# Each DAQpack is 24 bytes long


# Split the file up into the header and raw data.
# THIS needs tweaking, some log files will have a larger header,
# but data always begins at a multilpe of 0x400
headerData: List[List[str]] = [out.splitlines()
                               for out in data[:0x400].decode('utf-8').split('-----')]

rawData: bytes = data[0x400:]

splitData = []


def calcPressureCalibrationCoefs(header: List[List[str]]) -> PresCalType:
    """Calculate the calibration coeffiecents in the header.

    Args:
        header: The header file that contains the calibration data

    Returns:
        Calibration Coefficents for each pressure sensor

    """
    presCalibrations: PresCalType = {}
    for index, value in enumerate(header):

        # This part might not be necessary once we get the beginning of the raw
        # data down cold
        if "\x00\x00\x00" in value[0]:
            del header[index]

        elif "BME280 Temperature Humidity Pressure Sensor" in value[1]:
            sensorID: int = int(value[0].split(': ')[1])
            # This part is just for debugging at the moment. It lists BME280s
            print("Found a pressure sensor at index " + str(index))

            # Initialize a new entry in the dictionary of calibrations.
            presCalibrations[sensorID] = {}

            # Parse the calibration line to be only the characters that we want
            calString: str = (value[5].split(': ')[1])

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
                coefS16(calString, [54, 55, 52, 53]),
                coefU(calString, [56, 57]),

                coefS16(calString, [62, 63, 60, 61]),
                coefS16(calString, [66, 67, 64, 65]),

                coefS8(calString, [68, 69])]

    return presCalibrations


def splitSensorData(dataStream: bytes) -> UCompDataType:
    """Split the data stream apart into all sensors.

    Args:
        dataStream: The raw data to process and extract all sensor data from

    Returns:
        List off all packets with the uncompensated data parsed into a dictionary

    """
    # Seperate the Raw data into each packet
    # This seems to cut off the last data section right now
    try:
        for num in range(0, int(len(dataStream) / 24)):
            splitData.append(dataStream[24 * num:24 * num + 24])
    except Exception:
        print('err')

    # Split the information in each packet into the proper type
    uCompData: UCompDataType = []
    for index, value in enumerate(splitData):
        packetType: int = int.from_bytes(
            value[4:8], byteorder='little')
        if not packetType:
            # this is for packType == 0.
            # Undef, Means something weird happened and we need to check CPP
            # code for errors
            pass
        elif packetType == 0x01:
            pass
            # Timestamp packet. Talk to Dr. Davis
        elif packetType == 0x02:
            # This is for the Acclerometer. Currently uses signed short 16,
            # so we need to be careful about this one
            uCompData.append({'ID': int.from_bytes(value[0:4], byteorder='little'),
                              'type': packetType,
                              'uAccX': int.from_bytes(value[8:10], byteorder='little'),
                              'uAccY': int.from_bytes(value[10:12], byteorder='little'),
                              'uAccZ': int.from_bytes(value[12:14], byteorder='little')})

        elif packetType == 0x03:
            # Barotemp type packet. Used with the BMP180
            uCompData.append({
                'ID': value[0],
                'type': packetType,
                'uPres': int.from_bytes(value[8:12], byteorder='little'),
                'uTemp': int.from_bytes(value[12:14], byteorder='little')
            })
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
            uCompData[index] = {'ID': int.from_bytes(value[0:4],
                                                     byteorder='little'),
                                'type': packetType,
                                'uAccX': int.from_bytes(value[8:10], byteorder='little'),
                                'uAccY': int.from_bytes(value[10:12], byteorder='little'),
                                'uAcczZ': int.from_bytes(value[12:14], byteorder='little'),
                                'uGyroX': int.from_bytes(value[14:16], byteorder='little'),
                                'uGyroY': int.from_bytes(value[16:18], byteorder='little'),
                                'uGyroZ': int.from_bytes(value[18:20], byteorder='little'),
                                'uTemp': int.from_bytes(value[20:22], byteorder='little'),
                                }
        elif packetType == 0x08:
            # ADXL345_t currently unused in code (commit 182fe0c)
            pass
        elif packetType == 0x09:
            # BMP180_t currently unused (commit  182fe0c)
            pass
        elif packetType == 0x0a:
            # Prestemphuhid type packet. Used by BME280
            uCompData[index] = {'ID': int.from_bytes(value[0:4], byteorder='little'),
                                'type': packetType,
                                'uPres': int.from_bytes(value[8:12], byteorder='little'),
                                'uTemp': int.from_bytes(value[12:16], byteorder='little'),
                                'uHumid': int.from_bytes(value[16:18], byteorder='little')
                                }

        elif packetType == 0x0b:
            # HSCpress packet. Used by our relative pressure sensors (pitot tubes)

            # Currently has some issues with the status bit, waiting on Dr. Davis
            # For a solution

            uCompData[index] = {'ID': value[0],
                                'type': packetType,
                                # 'status': int.from_bytes(bytesvalue[])
                                # 'uPres': int.
                                }
        elif packetType == 0x0c:
            # DUAL_Clock_t unknown use
            pass
        elif packetType == 0x0d:
            pass

    return uCompData


# Packet Format is 1 byte ID for sensor, then a 4 byte ID for the packet type
# The rest of the bytes (19 of them) hold the data. The format for this changes
# Per sensor type. See eas_daq_pack.h in github repo for more info.

# print(item for item in uCompData if (item['ID'] == 2))
""""print(presCalibrations)
print([hex(i) for i in presCalibrations[2]['temperature']])
print([hex(i) for i in presCalibrations[2]['pressure']])
print([hex(i) for i in presCalibrations[2]['humidity']])"""
'''
for item in range(0, 20):
    print(splitData[item])
    print("\n")
    try:
        if uCompData[item]['ID'] == 2:
            print(uCompData[item])
    except:
        pass'''
