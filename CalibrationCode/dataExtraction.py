#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This is the top level file for the EAS Data extraction module.

It reads the calibration coefficents and the raw data from the EAS Log files,
organizes them, and calculates SI values for each raw data point, saving it as
in a form for other scripts to acces and operate on (such as saving to a file,
or graphing).
"""
# INFO: Each DAQpack is 24 bytes long

import binascii
import struct
from os import PathLike
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from typing import BinaryIO, Dict, List, Tuple, Union

# Type hint aliases
TempCoefsType = Tuple[int, int, int]
PresCoefsType = Tuple[int, int, int, int, int, int, int, int, int]
HumidityCoefsType = Tuple[int, int, int, int, int, int]
BME280CalType = Dict[Union[str, int], Dict[str, Union[TempCoefsType, PresCoefsType, HumidityCoefsType]]]
UCompDataType = List[Dict[str, Union[int]]]


def openFileInteractive() -> Tuple[List[List[str]], bytes]:
    """Open a tkinter file dialog to prompt the user to select a file, then parse the file.

    Returns:
        The header divided up into sections, and the raw data from the dump section.

    """
    data: bytes
    fileObj: BinaryIO
    Tk().withdraw()
    fileName = askopenfilename(title='Select File to Open', filetypes=(('Log File', '*.log'), ('All File Types', '*')))
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
        if '\x00\x00\x00' in value[0]:
            del header[index]

        elif 'BME280 Temperature Humidity Pressure Sensor' in value[1]:
            sensorID: int = int(value[0].split(': ')[1])
            # This part is just for debugging at the moment. It lists BME280s
            print('Found a pressure sensor at index ' + str(index))

            # Initialize a new entry in the dictionary of calibrations.
            presCalibrations[sensorID] = {}

            # Parse the calibration line to be only the characters that we want
            try:
                calString: str = (value[5].split(': ')[1])
            except IndexError:
                calString = (value[5].split('||')[1])

            # Calculate the temperature calibration values
            presCalibrations[sensorID]['temperature'] = struct.unpack(  # type: ignore
                'Hhh', binascii.unhexlify(calString[0:12]))

            # Calculate the Pressure calibration values
            presCalibrations[sensorID]['pressure'] = struct.unpack(  # type: ignore
                'Hhhhhhhhh', binascii.unhexlify(calString[12:48]))

            # Calculate the humidity calibrations values
            presCalibrations[sensorID]['humidity'] = struct.unpack(  # type: ignore
                'BhBhhb', binascii.unhexlify(calString[48:70]))

    return presCalibrations


def splitSensorData(dataStream: bytes) -> List[bytes]:
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
    # pylint: disable=too-complex, too-many-branches
    """Extract variables from the packets using the struct module.

    Args:
        packets: A list of byte string, where every byte string is one EAS packet

    Returns:
        List of dicts, where each dict is the uncompensated data extracted from the packet.

    """
    # Split the information in each packet into the proper type
    uCompData: UCompDataType = []
    names: Tuple[str, ...]
    for packet in packets:
        packetType: int = struct.unpack('<xxxxIxxxxxxxxxxxxxxxx', packet)[0]
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
            data = struct.unpack('<IIhhhxxxxxxxxxx', packet)
            names = ('ID', 'type', 'uAccX', 'uAccY', 'uAccZ')
            uCompData.append(dict(zip(names, data)))
        elif packetType == 0x03:
            # Barotemp type packet. Used with the BMP180
            data = struct.unpack('<IIIHxxxxxxxxxx', packet)
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
            data = struct.unpack('<IIhhhhhhhxx', packet)
            uCompData.append(dict(zip(names, data)))
        elif packetType == 0x08:
            # ADXL345_t currently unused in code (commit 182fe0c)
            pass
        elif packetType == 0x09:
            # BMP180_t currently unused (commit  182fe0c)
            pass
        elif packetType == 0x0a:
            data = struct.unpack('<IIIIHxxxxxx', packet)
            names = ('ID', 'type', 'uPres', 'uTemp', 'uHumid')

            uCompData.append(dict(zip(names, data)))
            # Prestemphuhid type packet. Used by BME280
        elif packetType == 0x0b:
            # HSCpress packet. Used by our relative pressure sensors (pitot tubes)

            # Currently has some issues with the status bit, waiting on Dr. Davis
            # For a solution

            uCompData.append({'ID': packet[0],
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
    extractPresCalCoefs(header)
    splitN = splitSensorData(rawDataN)
    processedPackets = processPackets(splitN)
    for i in processedPackets:
        print(i)
