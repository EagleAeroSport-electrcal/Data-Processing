"""Unit Tests for dataExtraction.py."""
import CalibrationCode.dataExtraction as dataExtraction
from pathlib import Path


def testMethodsIdentical() -> None:
    """Test the log files to make sure both extraction methods have the same result."""
    logDir: Path = Path('Test Logs')
    for file in logDir.iterdir():
        header, rawData = dataExtraction.openFileNonInteractive(file)
        split = dataExtraction.splitSensorData(rawData)
        oldMethod = dataExtraction.processPackets(split)
        newMethod = dataExtraction.processPacketsWithStruct(split)
        for i in range(len(oldMethod)):
            assert oldMethod[i] == newMethod[i]
