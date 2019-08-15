"""Unit Tests for dataExtraction.py."""
# pylint: disable=invalid-name
from pathlib import Path

import CalibrationCode.dataExtraction as dataExtraction


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
            assert set(sensor.keys()) == {'temperature', 'pressure', 'humidity'}
            for section in sensor.values():
                for coef in section:
                    assert isinstance(coef, int)


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
