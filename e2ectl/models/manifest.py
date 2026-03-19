"""Manifest models — the declarative YAML schema."""

from pydantic import BaseModel, model_validator


class ManifestMetadata(BaseModel):
    name: str
    site: str = ""
    project: str = ""
    integrator: str = ""
    contact: str = ""
    created: str = ""
    notes: str = ""


class ManifestCredentials(BaseModel):
    username: str = "root"
    password: str = ""


class Defaults(BaseModel):
    credentials: ManifestCredentials = ManifestCredentials()
    timeout: int = 10


class ManifestDevice(BaseModel):
    name: str
    ip: str
    type: str
    model: str = ""
    credentials: ManifestCredentials | None = None


class ManifestPairing(BaseModel):
    name: str
    type: str
    subtype: str | None = None
    primary: str
    secondary: str
    config: dict[str, str | int | float | bool] | None = None
    labels: dict[str, str] = {}


class SitePairing(BaseModel):
    """Top-level manifest model — the full YAML document."""

    apiVersion: str = "e2ectl/v1"  # noqa: N815 — matches YAML schema
    kind: str = "SitePairing"
    metadata: ManifestMetadata
    defaults: Defaults = Defaults()
    devices: list[ManifestDevice]
    pairings: list[ManifestPairing]

    @model_validator(mode="after")
    def validate_pairing_references(self) -> "SitePairing":
        """Ensure all pairing primary/secondary references exist in devices."""
        device_names = {d.name for d in self.devices}
        for p in self.pairings:
            if p.primary not in device_names:
                raise ValueError(
                    f"Pairing '{p.name}' references unknown primary device '{p.primary}'"
                )
            if p.secondary not in device_names:
                raise ValueError(
                    f"Pairing '{p.name}' references unknown secondary device '{p.secondary}'"
                )
        return self
