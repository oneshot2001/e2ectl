"""Device discovery — subnet scanning and classification."""

from e2ectl.discovery.classifier import classify_device
from e2ectl.discovery.scanner import scan_subnet

__all__ = ["classify_device", "scan_subnet"]
