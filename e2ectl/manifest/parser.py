"""Manifest YAML parser with Pydantic validation."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from e2ectl.manifest.interpolate import interpolate_env_vars
from e2ectl.models.manifest import SitePairing


class ManifestError(Exception):
    """Human-readable manifest parsing/validation error."""


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
    path = Path(path)

    if not path.exists():
        raise ManifestError(f"Manifest file not found: {path}")

    try:
        raw = path.read_text()
    except OSError as e:
        raise ManifestError(f"Cannot read manifest: {e}") from e

    # Interpolate env vars before YAML parsing
    try:
        interpolated = interpolate_env_vars(raw, strict=strict_env)
    except Exception as e:
        raise ManifestError(f"Environment variable error: {e}") from e

    # Parse YAML
    try:
        data = yaml.safe_load(interpolated)
    except yaml.YAMLError as e:
        raise ManifestError(f"Invalid YAML: {e}") from e

    if not isinstance(data, dict):
        raise ManifestError("Manifest must be a YAML mapping (not a list or scalar)")

    # Validate with Pydantic
    try:
        return SitePairing.model_validate(data)
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            errors.append(f"  {loc}: {err['msg']}")
        raise ManifestError("Manifest validation failed:\n" + "\n".join(errors)) from e
