"""E2E: context loader — schema discovery and instance browsing via CLI.

Requires at least one existing knowledge network with built data.
These tests are read-only (non-destructive) by default.
"""
from __future__ import annotations

import json

import pytest

from kweaver import KWeaverClient
from kweaver.cli.main import cli

pytestmark = pytest.mark.e2e

# cli_runner fixture is defined in tests/e2e/conftest.py


def test_kn_list_discovers_knowledge_networks(cli_runner):
    """kn list should return knowledge networks."""
    result = cli_runner.invoke(cli, ["kn", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    for kn in data:
        assert "id" in kn
        assert "name" in kn


def test_kn_export_returns_structure(kweaver_client: KWeaverClient, cli_runner):
    """kn export should return object types and relation types."""
    kns = kweaver_client.knowledge_networks.list()
    if not kns:
        pytest.skip("No knowledge networks available")
    result = cli_runner.invoke(cli, ["kn", "export", kns[0].id])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, dict)


def test_query_instances_returns_data(kweaver_client: KWeaverClient, cli_runner):
    """query instances should return data rows."""
    kns = kweaver_client.knowledge_networks.list()
    if not kns:
        pytest.skip("No knowledge networks available")
    kn = kns[0]
    ots = kweaver_client.object_types.list(kn.id)
    if not ots:
        pytest.skip("No object types available")
    ot = ots[0]
    result = cli_runner.invoke(cli, [
        "query", "instances", kn.id, ot.id, "--limit", "5",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "data" in data
