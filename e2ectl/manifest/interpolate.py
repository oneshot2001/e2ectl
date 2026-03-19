"""Environment variable interpolation for manifest YAML files."""

from __future__ import annotations

import os
import re

_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")


class InterpolationError(Exception):
    """Raised when an env var referenced in a manifest is not set."""


def interpolate_env_vars(text: str, strict: bool = True) -> str:
    """Replace ${VAR_NAME} patterns with environment variable values.

    Args:
        text: Raw YAML text potentially containing ${VAR} references.
        strict: If True, raise InterpolationError for undefined vars.
                If False, leave undefined vars as empty strings.

    Returns:
        Text with all ${VAR} patterns replaced.

    Raises:
        InterpolationError: If strict=True and a referenced var is not set.
    """
    missing: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            if strict:
                missing.append(var_name)
                return match.group(0)
            return ""
        return value

    result = _ENV_PATTERN.sub(_replace, text)

    if missing:
        raise InterpolationError(
            f"Undefined environment variable(s): {', '.join(missing)}. "
            f"Set them or use strict=False."
        )

    return result
