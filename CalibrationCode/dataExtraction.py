"""This is the top level file for the EAS Data extraction module.

It reads the calibration coefficents and the raw data from the EAS Log files,
organizes them, and calculates SI values for each raw data point, saving it as
in a form for other scripts to acces and operate on (such as saving to a file,
or graphing).
"""
# INFO: Each DAQpack is 24 bytes long

import struct
from os import PathLike
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from typing import Any, BinaryIO, Dict, Iterable, List, Tuple, Union

# Type hint aliases
TempCoefsType = Tuple[int, int, int]
PresCoefsType = Tuple[int, int, int, int, int, int, int, int, int]
HumidityCoefsType = Tuple[int, int, int, int, int, int]
BME280CalType = Dict[Union[str, int], Dict[str, Union[TempCoefsType, PresCoefsType, HumidityCoefsType]]]
UCompDataType = List[Dict[str, Union[int]]]


# Nesting in try blocks to see if the code is being run from a system with top
# level as github repo


def openFileInteractive() -> Tuple[List[List[str]], bytes]:
    """Open a tkinter file dialog to prompt the user to select a file, then parse the file.

    Returns:
        The header divided up into sections, and the raw data from the dump section.

    """
    data: bytes
    f: BinaryIO
    """
    try:
        with open('easRV12_15_Nov_2018_21_15_33.log', 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        with open('CalibrationCode\\easRV12_15_Nov_2018_21_15_33.log', 'rb') as f:
            data = f.read()"""
    Tk().withdraw()
    fileName = askopenfilename(title='Select File to Open', filetypes=(("Log File", '*.log'), ('All File Types', '*')))
    with open(fileName, mode='rb') as fileObj:
        data = fileObj.read()

    # Each DAQpack is 24 bytes long

    # Split the file up into the header and raw data.
    # THIS needs tweaking, some log files will have a larger header,
    # but data always begins at a multilpe of 0x400

    return splitBytesFile(data)


def openFileNonInteractive(filePath: Union[str, PathLike]) -> Tuple[List[List[str]], bytes]:
    """Open and split up the given log file.

    Args:
        filePath: The path to the log file

    Returns:
        The header (split into section for each device), and the raw bytes from the data.

    """

    with open(filePath, mode='rb') as fileObj:
        data = fileObj.read()

    return splitBytesFile(data)


def splitBytesFile(bytesFile: bytes) -> Tuple[List[List[str]], bytes]:
    """Split up the raw data from a log file into the header and rawData.

    Args:
        bytesFile: The raw (in bytes) contents of a log file to split up.

    Returns:
        A list containing all section of the header where each section is then brokem up by line
        The raw data from the log file, still in bytes form

    """
    # Split the file up into the header and raw data.
    # THIS needs tweaking, some log files will have a larger header,
    # but data always begins at a multilpe of 0x400
    header: List[List[str]] = [out.splitlines() for out in bytesFile[:0x400].decode('utf-8').split('-----')]
    rawData: bytes = bytesFile[0x400:]
    return header, rawData


def coefU(string: str, locations: Iterable[int]) -> int:
    """Get an unsigned int from the provided string.

    Args:
        string: The string to extract the number from
        locations: The indices in the string that the number exists at

    Returns:
        Unsigned 16 bit integer

    """
    return int(''.join([string[element] for element in locations]), 16)


def coefS16(string: str, locations: Iterable[int]) -> int:
    """Get a signed 16-bit value from the provided string.

    Args:
        string: The string to extract the value from
        locations: The indices in the string to extract the value from

    Returns:
        Signed 16 bit integer

    """
    result = coefU(string, locations)
    if result > 32767:
        result -= 65536
    return result


def coefS8(string: str, locations: Iterable[int]) -> int:
    """Get a signed 8-bit value from the provided string.

    Args:
        string: The string to get the number from.
        locations: The indices in the string to extract the value from.

    Returns:
        Signed 8 bit integer

    """
    result = coefU(string, locations)
    if result > 127:
        result -= 256
    return result


def extractPresCalCoefs(header: List[List[str]]) -> BME280CalType:
    """Calculate the calibration coeffiecents in the header.

    Args:
        header: The header file that contains the calibration data

    Returns:
        Calibration Coefficents for each pressure sensor

    """
    presCalibrations: BME280CalType = {}
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
            try:
                calString: str = (value[5].split(': ')[1])
            except IndexError:
                calString = (value[5].split('||')[1])

            # Calculate the temperature calibration values
            presCalibrations[sensorID]['temperature'] = (
                coefU(calString, [2, 3, 0, 1]),
                coefS16(calString, [6, 7, 4, 5]),
                coefS16(calString, [10, 11, 8, 9])
            )

            # Calculate the Pressure calibration values
            presCalibrations[sensorID]['pressure'] = (
                coefU(calString, [14, 15, 12, 13]),
                coefS16(calString, [18, 19, 16, 17]),
                coefS16(calString, [22, 23, 20, 21]),
                coefS16(calString, [26, 27, 24, 25]),
                coefS16(calString, [31, 30, 28, 29]),
                coefS16(calString, [34, 35, 32, 33]),
                coefS16(calString, [38, 39, 36, 37]),
                coefS16(calString, [42, 43, 40, 41]),
                coefS16(calString, [46, 47, 44, 45])
            )

            # Calculate the humidity calibrations values
            presCalibrations[sensorID]['humidity'] = (
                coefU(calString, [48, 49]),
                coefS16(calString, [54, 55, 52, 53]),
                coefU(calString, [56, 57]),

                coefS16(calString, [62, 63, 60, 61]),
                coefS16(calString, [66, 67, 64, 65]),

                coefS8(calString, [68, 69])
            )

    return presCalibrations


def splitSensorData(dataStream: bytes) -> List[bytes]:        # pylint: disable=too-complex, too-many-branches
    """Split the data stream apart into all sensors.

    Args:
        dataStream: The raw data to process and extract all sensor data from

    Returns:
        List off all packets with the uncompensated data parsed into a dictionary

    """
    # Seperate the Raw data into each packet
    # This seems to cut off the last data section right now
    splitData: List[bytes] = []
    for num in range(0, int(len(dataStream) / 24)):
        splitData.append(dataStream[24 * num:24 * num + 24])
    return splitData


def processPackets(packets: List[bytes]) -> UCompDataType:
    """Extract variables from the packets using the struct module.

    Args:
        packets: A list of byte string, where every byte string is one EAS packet

    Returns:
        List of dicts, where each dict is the uncompensated data extracted from the packet.

    """
    # Split the information in each packet into the proper type
    uCompData: UCompDataType = []
    names: Tuple[str, ...]
    for index, value in enumerate(packets):
        packetType: int = struct.unpack('<xxxxIxxxxxxxxxxxxxxxx', value)[0]
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
            # so we need to be careful about this one.
            data = struct.unpack('<IIhhhxxxxxxxxxx', value)
            names = ('ID', 'type', 'uAccX', 'uAccY', 'uAccZ')
            uCompData.append(dict(zip(names, data)))
        elif packetType == 0x03:
            # Barotemp type packet. Used with the BMP180
            data = struct.unpack('<IIIHxxxxxxxxxx', value)
            names = ('ID', 'type', 'uPres', 'uTemp')
            uCompData.append(dict(zip(names, data)))
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
            names = ('ID', 'type', 'uAccX', 'uAccY', 'uAccZ', 'uGyroX', 'uGyroY', 'uGyroZ', 'uTemp')
            data = struct.unpack('<IIhhhhhhhxx', value)
            uCompData.append(dict(zip(names, data)))
        elif packetType == 0x08:
            # ADXL345_t currently unused in code (commit 182fe0c)
            pass
        elif packetType == 0x09:
            # BMP180_t currently unused (commit  182fe0c)
            pass
        elif packetType == 0x0a:
            data = struct.unpack('<IIIIHxxxxxx', value)
            names = ('ID', 'type', 'uPres', 'uTemp', 'uHumid')

            uCompData.append(dict(zip(names, data)))
            # Prestemphuhid type packet. Used by BME280
        elif packetType == 0x0b:
            # HSCpress packet. Used by our relative pressure sensors (pitot tubes)

            # Currently has some issues with the status bit, waiting on Dr. Davis
            # For a solution

            uCompData.append({'ID': value[0],
                              'type': packetType,
                              # 'status': int.from_bytes(bytesvalue[])
                              # 'uPres': int.
                              })
        elif packetType == 0x0c:
            # DUAL_Clock_t unknown use
            pass
        elif packetType == 0x0d:
            pass

    return uCompData  # Packet Format is 1 byte ID for sensor, then a 4 byte ID for the packet type
# The rest of the bytes (19 of them) hold the data. The format for this changes
# Per sensor type. See eas_daq_pack.h in github repo for more info.


# Run this if the module is run manually.
if __name__ == '__main__':
    header, rawDataN = openFileNonInteractive('Test Logs/easRV12_28_Oct_2016_04_39_20.log')
    splitN = splitSensorData(rawDataN)
    x = extractPresCalCoefs(header)
    processedPackets = processPackets(splitN)
    for i in processedPackets:
        print(i)
