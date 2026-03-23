"""Tests for kweaver use context command."""
from __future__ import annotations

import json

import click
import pytest
from click.testing import CliRunner
from kweaver.cli.main import cli


def _set_fake_home(monkeypatch, tmp_path) -> None:
    """Redirect Path.home() on all platforms (Windows uses USERPROFILE, not HOME)."""
    home = str(tmp_path)
    monkeypatch.setenv("HOME", home)
    monkeypatch.setenv("USERPROFILE", home)


def test_use_set(tmp_path, monkeypatch):
    """kweaver use <kn_id> saves context."""
    _set_fake_home(monkeypatch, tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["use", "kn-abc123"])
    assert result.exit_code == 0
    assert "kn-abc123" in result.output

    ctx_file = tmp_path / ".kweaver" / "context.json"
    assert ctx_file.exists()
    data = json.loads(ctx_file.read_text(encoding="utf-8"))
    assert data["kn_id"] == "kn-abc123"


def test_use_show(tmp_path, monkeypatch):
    """kweaver use (no args) shows current context."""
    _set_fake_home(monkeypatch, tmp_path)
    ctx_dir = tmp_path / ".kweaver"
    ctx_dir.mkdir()
    (ctx_dir / "context.json").write_text(
        json.dumps({"kn_id": "kn-abc123"}), encoding="utf-8", newline="\n",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["use"])
    assert result.exit_code == 0
    assert "kn-abc123" in result.output


def test_use_clear(tmp_path, monkeypatch):
    """kweaver use --clear removes context."""
    _set_fake_home(monkeypatch, tmp_path)
    ctx_dir = tmp_path / ".kweaver"
    ctx_dir.mkdir()
    (ctx_dir / "context.json").write_text(
        json.dumps({"kn_id": "kn-abc123"}), encoding="utf-8", newline="\n",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["use", "--clear"])
    assert result.exit_code == 0


def test_use_show_no_context(tmp_path, monkeypatch):
    """kweaver use with no saved context shows helpful message."""
    _set_fake_home(monkeypatch, tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["use"])
    assert result.exit_code == 0


# --- resolve_kn_id tests ---

from kweaver.cli._helpers import resolve_kn_id


def test_resolve_kn_id_explicit_arg():
    """Explicit arg takes priority over context."""
    assert resolve_kn_id("kn-explicit") == "kn-explicit"


def test_resolve_kn_id_from_context(tmp_path, monkeypatch):
    """Falls back to context file when no arg given."""
    _set_fake_home(monkeypatch, tmp_path)
    ctx_dir = tmp_path / ".kweaver"
    ctx_dir.mkdir()
    (ctx_dir / "context.json").write_text(
        json.dumps({"kn_id": "kn-from-ctx"}), encoding="utf-8", newline="\n",
    )
    assert resolve_kn_id(None) == "kn-from-ctx"


def test_resolve_kn_id_raises_when_neither(tmp_path, monkeypatch):
    """Raises UsageError when no arg and no context."""
    _set_fake_home(monkeypatch, tmp_path)
    with pytest.raises(click.UsageError, match="kn_id"):
        resolve_kn_id(None)
