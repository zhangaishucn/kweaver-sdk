"""CLI: action type commands."""

from __future__ import annotations

import json

import click

from kweaver.cli._helpers import error_exit, handle_errors, make_client, pp


@click.group("action")
def action_group() -> None:
    """Manage action types."""


@action_group.command("query")
@click.argument("kn_id")
@click.argument("action_type_id")
@handle_errors
def query_action(kn_id: str, action_type_id: str) -> None:
    """Query an action type definition."""
    client = make_client()
    data = client.action_types.query(kn_id, action_type_id)
    pp(data)


@action_group.command("execute")
@click.argument("kn_id")
@click.argument("action_type_id", required=False, default=None)
@click.option("--action-name", default=None, help="Resolve action type by name (via kn_search).")
@click.option("--params", "params_json", default=None, help="JSON execution parameters.")
@click.option("--wait/--no-wait", default=True)
@click.option("--timeout", default=300, type=int)
@handle_errors
def execute_action(kn_id: str, action_type_id: str | None, action_name: str | None,
                   params_json: str | None, wait: bool, timeout: int) -> None:
    """Execute an action type."""
    client = make_client()
    if not action_type_id and not action_name:
        error_exit("Either ACTION_TYPE_ID or --action-name must be provided")
    if action_name and not action_type_id:
        search_result = client.query.kn_search(kn_id, action_name)
        actions = search_result.action_types or []
        if not actions:
            error_exit(f"Action type '{action_name}' not found")
        action_type_id = actions[0]["id"]
    params = json.loads(params_json) if params_json else None

    execution = client.action_types.execute(kn_id, action_type_id, params=params)
    click.echo(f"Execution started: {execution.execution_id}")

    if wait:
        click.echo("Waiting for completion ...")
        result = execution.wait(timeout=timeout)
        click.echo(f"Status: {result.status}")
        if result.result:
            pp(result.result)
    else:
        click.echo(f"Status: {execution.status}")


@action_group.command("logs")
@click.argument("kn_id")
@click.option("--limit", default=20, type=int)
@handle_errors
def list_logs(kn_id: str, limit: int) -> None:
    """List action execution logs."""
    client = make_client()
    logs = client.action_types.list_logs(kn_id, limit=limit)
    pp(logs)


@action_group.command("log")
@click.argument("kn_id")
@click.argument("log_id")
@handle_errors
def get_log(kn_id: str, log_id: str) -> None:
    """Get a single execution log."""
    client = make_client()
    data = client.action_types.get_log(kn_id, log_id)
    pp(data)
