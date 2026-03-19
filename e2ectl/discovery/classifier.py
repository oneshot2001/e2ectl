"""Rule-based device type classification from Axis model numbers."""

import re

from e2ectl.models.device import DeviceType

# Patterns ordered by specificity. First match wins.
_RULES: list[tuple[re.Pattern[str], DeviceType]] = [
    # Radars
    (re.compile(r"AXIS D2\d{3}", re.IGNORECASE), DeviceType.RADAR),
    # Intercoms
    (re.compile(r"AXIS A(81|82|83|84|85|86)\d{2}", re.IGNORECASE), DeviceType.INTERCOM),
    # Speakers (C-series)
    (re.compile(r"AXIS C1[1-9]\d{2}", re.IGNORECASE), DeviceType.SPEAKER),
    (re.compile(r"AXIS C\d{4}", re.IGNORECASE), DeviceType.SPEAKER),
    # Strobe sirens
    (re.compile(r"AXIS D4100", re.IGNORECASE), DeviceType.STROBE),
    # Microphones (standalone — rare, usually built into cameras)
    (re.compile(r"AXIS TU1001", re.IGNORECASE), DeviceType.MICROPHONE),
    # Cameras — broad catch-all for P, Q, M, FA series etc.
    (re.compile(r"AXIS (P|Q|M|FA|F)\d{3,4}", re.IGNORECASE), DeviceType.CAMERA),
]


def classify_device(model: str) -> DeviceType:
    """Classify an Axis device type from its model string.

    Args:
        model: Model name, e.g. "AXIS P3268-LVE" or "AXIS C1410".

    Returns:
        The classified DeviceType, or DeviceType.UNKNOWN if no rule matches.
    """
    for pattern, device_type in _RULES:
        if pattern.search(model):
            return device_type
    return DeviceType.UNKNOWN
