"""E2E: Vega metadata read operations."""
import pytest
from kweaver.types import VegaCatalog, VegaConnectorType

pytestmark = pytest.mark.e2e


def test_vega_health(vega_client):
    """SDK: vega health returns server info."""
    info = vega_client.health()
    assert info.server_name
    assert info.server_version


def test_vega_catalog_list(vega_client):
    """SDK: list catalogs."""
    cats = vega_client.catalogs.list()
    assert isinstance(cats, list)
    if cats:
        assert isinstance(cats[0], VegaCatalog)


def test_vega_connector_type_list(vega_client):
    """SDK: list connector types."""
    types = vega_client.connector_types.list()
    assert isinstance(types, list)
    assert len(types) > 0  # built-in types always exist


def test_vega_resource_list(vega_client):
    """SDK: list resources."""
    resources = vega_client.resources.list(limit=5)
    assert isinstance(resources, list)


def test_vega_inspect(vega_client):
    """SDK: inspect returns aggregated report."""
    from kweaver.types import VegaInspectReport
    report = vega_client.inspect()
    assert isinstance(report, VegaInspectReport)
