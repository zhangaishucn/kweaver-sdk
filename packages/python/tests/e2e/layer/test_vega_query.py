"""E2E: Vega query operations."""
import pytest
from kweaver.types import VegaDslResult

pytestmark = pytest.mark.e2e


def test_query_dsl(vega_client):
    """DSL search — may skip if no index data."""
    try:
        result = vega_client.query.dsl(body={"query": {"match_all": {}}, "size": 1})
        assert isinstance(result, VegaDslResult)
    except Exception:
        pytest.skip("No DSL-compatible data source")


def test_vega_task_list_discover(vega_client):
    """List discover tasks."""
    tasks = vega_client.tasks.list_discover()
    assert isinstance(tasks, list)
