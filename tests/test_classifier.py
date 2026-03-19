"""Tests for device type classification."""

import pytest

from e2ectl.discovery.classifier import classify_device
from e2ectl.models.device import DeviceType


@pytest.mark.parametrize(
    "model,expected",
    [
        # Cameras
        ("AXIS P3268-LVE", DeviceType.CAMERA),
        ("AXIS P3265-LVE", DeviceType.CAMERA),
        ("AXIS Q1786-LE", DeviceType.CAMERA),
        ("AXIS M3106-LVE Mk II", DeviceType.CAMERA),
        ("AXIS FA4115", DeviceType.CAMERA),
        ("AXIS F1004", DeviceType.CAMERA),
        # Speakers
        ("AXIS C1410", DeviceType.SPEAKER),
        ("AXIS C1310-E", DeviceType.SPEAKER),
        ("AXIS C1110-E", DeviceType.SPEAKER),
        ("AXIS C8210", DeviceType.SPEAKER),
        # Radars
        ("AXIS D2210-VE", DeviceType.RADAR),
        ("AXIS D2110-VE", DeviceType.RADAR),
        # Intercoms
        ("AXIS A8105-E", DeviceType.INTERCOM),
        ("AXIS A8207-VE", DeviceType.INTERCOM),
        # Strobes
        ("AXIS D4100-E", DeviceType.STROBE),
        # Unknown
        ("Some Random Device", DeviceType.UNKNOWN),
        ("", DeviceType.UNKNOWN),
    ],
)
def test_classify_device(model: str, expected: DeviceType):
    assert classify_device(model) == expected


def test_classification_is_case_insensitive():
    assert classify_device("axis p3268-lve") == DeviceType.CAMERA
    assert classify_device("AXIS C1410") == DeviceType.SPEAKER
