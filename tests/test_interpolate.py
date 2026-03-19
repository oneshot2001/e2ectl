"""Tests for environment variable interpolation."""


import pytest

from e2ectl.manifest.interpolate import InterpolationError, interpolate_env_vars


def test_basic_interpolation(monkeypatch):
    monkeypatch.setenv("MY_VAR", "hello")
    assert interpolate_env_vars("value: ${MY_VAR}") == "value: hello"


def test_multiple_vars(monkeypatch):
    monkeypatch.setenv("USER", "root")
    monkeypatch.setenv("PASS", "secret")
    result = interpolate_env_vars("${USER}:${PASS}")
    assert result == "root:secret"


def test_undefined_var_strict():
    with pytest.raises(InterpolationError, match="NONEXISTENT"):
        interpolate_env_vars("${NONEXISTENT}", strict=True)


def test_undefined_var_lenient():
    result = interpolate_env_vars("password: ${NONEXISTENT}", strict=False)
    assert result == "password: "


def test_no_vars():
    text = "plain text with no variables"
    assert interpolate_env_vars(text) == text


def test_partial_match_not_interpolated():
    text = "this is $NOT_A_VAR and ${THIS_IS}"
    # $NOT_A_VAR should be left alone, ${THIS_IS} should be caught
    with pytest.raises(InterpolationError):
        interpolate_env_vars(text, strict=True)


def test_preserves_yaml_structure(monkeypatch):
    monkeypatch.setenv("E2ECTL_DEFAULT_PASS", "test123")
    yaml_text = """defaults:
  credentials:
    username: root
    password: ${E2ECTL_DEFAULT_PASS}
  timeout: 15"""
    result = interpolate_env_vars(yaml_text)
    assert "test123" in result
    assert "${E2ECTL_DEFAULT_PASS}" not in result
