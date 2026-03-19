"""CLI integration tests using Click's test runner."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from e2ectl.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "e2ectl" in result.output
    assert "0.1.0" in result.output


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "discover" in result.output
    assert "plan" in result.output
    assert "apply" in result.output
    assert "verify" in result.output
    assert "teardown" in result.output


def test_plan_valid_manifest(monkeypatch: object):

    monkeypatch.setenv("E2ECTL_DEFAULT_PASS", "test123")  # type: ignore[attr-defined]

    runner = CliRunner()
    result = runner.invoke(cli, ["plan", "-f", str(FIXTURES / "retail-store.yaml")])
    assert result.exit_code == 0
    assert "Walgreens" in result.output
    assert "entrance-deterrence" in result.output
    assert "Manifest is valid" in result.output


def test_plan_missing_manifest():
    runner = CliRunner()
    result = runner.invoke(cli, ["plan", "-f", "/nonexistent/path.yaml"])
    assert result.exit_code == 3


def test_apply_dry_run(monkeypatch: object):
    monkeypatch.setenv("E2ECTL_DEFAULT_PASS", "test123")  # type: ignore[attr-defined]

    runner = CliRunner()
    result = runner.invoke(
        cli, ["--dry-run", "apply", "-f", str(FIXTURES / "retail-store.yaml")]
    )
    assert result.exit_code == 0
    assert "Dry run" in result.output
    assert "Manifest is valid" in result.output


def test_discover_requires_range():
    runner = CliRunner()
    result = runner.invoke(cli, ["discover"])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_plan_with_radar_manifest(monkeypatch: object):
    monkeypatch.setenv("E2ECTL_DEFAULT_PASS", "test123")  # type: ignore[attr-defined]

    runner = CliRunner()
    result = runner.invoke(
        cli, ["plan", "-f", str(FIXTURES / "radar-campus.yaml")]
    )
    assert result.exit_code == 0
    assert "radar-ptz" in result.output
    assert "Manifest is valid" in result.output
