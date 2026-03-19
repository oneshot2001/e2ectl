"""Tests for manifest parsing and validation."""

from pathlib import Path

import pytest

from e2ectl.manifest.parser import ManifestError, load_manifest
from e2ectl.models.manifest import SitePairing

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_retail_store(monkeypatch):
    monkeypatch.setenv("E2ECTL_DEFAULT_PASS", "test123")
    manifest = load_manifest(FIXTURES / "retail-store.yaml")

    assert isinstance(manifest, SitePairing)
    assert manifest.metadata.name == "walgreens-store-4421"
    assert len(manifest.devices) == 6
    assert len(manifest.pairings) == 3


def test_device_count(monkeypatch):
    monkeypatch.setenv("E2ECTL_DEFAULT_PASS", "test123")
    manifest = load_manifest(FIXTURES / "retail-store.yaml")

    cameras = [d for d in manifest.devices if d.type == "camera"]
    speakers = [d for d in manifest.devices if d.type == "speaker"]
    assert len(cameras) == 3
    assert len(speakers) == 3


def test_pairing_references_valid(monkeypatch):
    monkeypatch.setenv("E2ECTL_DEFAULT_PASS", "test123")
    manifest = load_manifest(FIXTURES / "retail-store.yaml")

    device_names = {d.name for d in manifest.devices}
    for p in manifest.pairings:
        assert p.primary in device_names
        assert p.secondary in device_names


def test_pairing_labels(monkeypatch):
    monkeypatch.setenv("E2ECTL_DEFAULT_PASS", "test123")
    manifest = load_manifest(FIXTURES / "retail-store.yaml")

    entrance = next(p for p in manifest.pairings if p.name == "entrance-deterrence")
    assert entrance.labels["zone"] == "entrance"
    assert entrance.labels["purpose"] == "deterrence"


def test_invalid_pairing_reference(tmp_path):
    bad_manifest = tmp_path / "bad.yaml"
    bad_manifest.write_text("""
apiVersion: e2ectl/v1
kind: SitePairing
metadata:
  name: test
devices:
  - name: cam1
    ip: 10.0.0.1
    type: camera
pairings:
  - name: bad-pair
    type: audio
    primary: cam1
    secondary: nonexistent
""")
    with pytest.raises(ManifestError, match="nonexistent"):
        load_manifest(bad_manifest, strict_env=False)


def test_missing_file():
    with pytest.raises(ManifestError, match="not found"):
        load_manifest("/nonexistent/path.yaml")


def test_env_var_interpolation(monkeypatch):
    monkeypatch.setenv("E2ECTL_DEFAULT_PASS", "my_secret")
    manifest = load_manifest(FIXTURES / "retail-store.yaml")
    assert manifest.defaults.credentials.password == "my_secret"
