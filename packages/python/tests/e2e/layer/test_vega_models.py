"""E2E: Vega model resources — parameterized."""
import pytest

pytestmark = pytest.mark.e2e

MODEL_ATTRS = [
    "metric_models",
    "event_models",
    "trace_models",
    "data_views",
    "data_dicts",
    "objective_models",
]


@pytest.mark.parametrize("attr", MODEL_ATTRS)
def test_model_list(vega_client, attr):
    result = getattr(vega_client, attr).list(limit=5)
    assert isinstance(result, list)


@pytest.mark.parametrize("attr", MODEL_ATTRS)
def test_model_get(vega_client, attr):
    items = getattr(vega_client, attr).list(limit=1)
    if not items:
        pytest.skip(f"No {attr} available")
    item = getattr(vega_client, attr).get(items[0].id)
    assert item.id == items[0].id
