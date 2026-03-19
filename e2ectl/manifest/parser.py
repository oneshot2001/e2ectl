"""Manifest YAML parser with Pydantic validation.

Uses axelib for YAML loading + env var interpolation, keeps e2ectl-specific
Pydantic validation on top.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from axelib.manifest.loader import ManifestError, load_yaml  # noqa: F401
from pydantic import ValidationError

from e2ectl.models.manifest import SitePairing

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["ManifestError", "load_manifest"]


def load_manifest(path: str | Path, strict_env: bool = True) -> SitePairing:
    """Load and validate a manifest YAML file.

    Args:
        path: Path to the YAML manifest file.
        strict_env: If True, fail on undefined env vars. If False, replace with empty string.

    Returns:
        A validated SitePairing model.

    Raises:
        ManifestError: On file read, YAML parse, or validation failure.
    """
    data = load_yaml(path, strict_env=strict_env)

    # Validate with Pydantic
    try:
        return SitePairing.model_validate(data)
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            errors.append(f"  {loc}: {err['msg']}")
        raise ManifestError("Manifest validation failed:\n" + "\n".join(errors)) from e
