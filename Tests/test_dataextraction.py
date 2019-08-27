"""Unit Tests for dataExtraction.py."""
# pylint: disable=invalid-name
from pathlib import Path

from CalibrationCode import dataExtraction
from dataclasses import astuple


def test_fileSplitWorks() -> None:
    """Test all the file opening and splitting function."""
    logDir: Path = Path('Test Logs')
    for file in logDir.iterdir():
        header, rawData = dataExtraction.openFileNonInteractive(file)
        assert isinstance(header, list)
        for section in header:
            assert isinstance(section, list)
            for line in section:
                assert isinstance(line, str)
        assert isinstance(rawData, bytes)


def test_extractPresCalCoefsWorks() -> None:
    """Test if the pressure calibration coefficent extractor function works."""
    logDir: Path = Path('Test Logs')
    for file in logDir.iterdir():
        header, _ = dataExtraction.openFileNonInteractive(file)
        calCoefs = dataExtraction.extractPresCalCoefs(header)
        assert isinstance(calCoefs, dict)
        for sensor in calCoefs.values():
            assert sorted((i for i in dir(sensor) if not i.startswith('_'))) == sorted(
                ('temperature', 'pressure', 'humidity', 'ID'))
            assert len(sensor.temperature) == 3
            for element in sensor.temperature:
                assert isinstance(element, int)
            assert len(sensor.pressure) == 9
            for element in sensor.pressure:
                assert isinstance(element, int)
            assert len(sensor.humidity) == 6
            for element in sensor.pressure:
                assert isinstance(element, int)
            assert isinstance(sensor.ID, int)


def test_splitDataWorks() -> None:
    """Test if the splitData function works."""
    logDir: Path = Path('Test Logs')
    for file in logDir.iterdir():
        _, rawData = dataExtraction.openFileNonInteractive(file)
        splitData = dataExtraction.splitSensorData(rawData)
        assert isinstance(splitData, list)
        for packet in splitData:
            assert isinstance(packet, bytes)
            assert len(packet) == 24


def test_extractPacketDataWorks() -> None:
    """Test if the packet value extractor works."""
    _, rawDataN = dataExtraction.openFileNonInteractive('Test Logs/easRV12_28_Oct_2016_04_39_20.log')
    splitN = dataExtraction.splitSensorData(rawDataN)
    processedPackets = dataExtraction.processPackets(splitN)
    assert isinstance(processedPackets, list)
    for packet in processedPackets:
        assert isinstance(packet, dict)
        validKeys = {'ID', 'type', 'uPres', 'uTemp', 'uHumid', 'uAccX',
                     'uAccY', 'uAccZ', 'uGyroX', 'uGyroY', 'uGyroZ', 'uHSCPress'}
        for key, value in packet.items():
            assert key in validKeys
            assert isinstance(value, int)
