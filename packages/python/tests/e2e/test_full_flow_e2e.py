"""E2E: full flow — connect database -> build knowledge network -> query.

Exercises the complete lifecycle through CLI commands.
Destructive: creates and deletes datasources, knowledge networks, etc.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from kweaver import KWeaverClient
from kweaver.cli.main import cli

pytestmark = [pytest.mark.e2e, pytest.mark.destructive]


def _extract_json(output: str) -> Any:
    """Extract JSON object/array from CLI output that may contain non-JSON lines."""
    # Try parsing the entire output first
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass
    # Find the first { or [ and parse from there
    for i, ch in enumerate(output):
        if ch in "{[":
            try:
                return json.loads(output[i:])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"No JSON found in output: {output[:200]}")


def test_cli_full_lifecycle(kweaver_client: KWeaverClient, db_config: dict[str, Any], cli_runner):
    """End-to-end: ds connect -> kn create -> query search."""
    runner = cli_runner
    kn_name = "e2e_full_flow_kn"
    # Clean up stale KN from previous runs
    for kn in kweaver_client.knowledge_networks.list(name=kn_name):
        if kn.name == kn_name:
            try:
                kweaver_client.knowledge_networks.delete(kn.id)
            except Exception:
                pass

    # Step 1: ds connect
    connect_args = [
        "ds", "connect", db_config["type"],
        db_config["host"], str(db_config["port"]), db_config["database"],
        "--account", db_config["account"],
        "--password", db_config["password"],
    ]
    if db_config.get("schema"):
        connect_args += ["--schema", db_config["schema"]]
    connect_result = runner.invoke(cli, connect_args)
    assert connect_result.exit_code == 0, f"ds connect failed: {connect_result.output}"
    connect_data = _extract_json(connect_result.output)
    ds_id = connect_data["datasource_id"]
    assert len(connect_data["tables"]) > 0
    first_table = connect_data["tables"][0]["name"]
    kn_id = None

    try:
        # Step 2: kn create
        create_result = runner.invoke(cli, [
            "kn", "create", ds_id, "--name", kn_name, "--tables", first_table,
        ])
        assert create_result.exit_code == 0, f"kn create failed: {create_result.output}"
        create_data = _extract_json(create_result.output)
        kn_id = create_data["kn_id"]
        assert create_data["status"] in ("completed", "failed")
        assert len(create_data["object_types"]) == 1

        # Step 3: kn export
        export_result = runner.invoke(cli, ["kn", "export", kn_id])
        assert export_result.exit_code == 0

        # Step 4: query search (if build succeeded)
        if create_data["status"] == "completed":
            search_result = runner.invoke(cli, ["query", "search", kn_id, first_table])
            assert search_result.exit_code == 0
    finally:
        if kn_id:
            try:
                kweaver_client.knowledge_networks.delete(kn_id)
            except Exception:
                pass
        try:
            kweaver_client.datasources.delete(ds_id)
        except Exception:
            pass
