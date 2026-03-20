"""Tests for deep get() — full property parsing."""
import httpx
from tests.conftest import RequestCapture, make_client


def test_object_type_get_parses_data_properties(capture: RequestCapture):
    """get() should parse data_properties from API response."""
    def handler(req):
        return httpx.Response(200, json={
            "id": "ot-1", "name": "Pod", "kn_id": "kn-1",
            "data_properties": [
                {"name": "cpu", "type": "float", "indexed": True, "mapped_field": "cpu_cores"},
                {"name": "name", "type": "string"},
            ],
        })
    client = make_client(handler, capture)
    ot = client.object_types.get("kn-1", "ot-1")
    assert len(ot.data_properties) == 2
    assert ot.data_properties[0].name == "cpu"
    assert ot.data_properties[0].indexed is True
    assert ot.data_properties[0].mapped_field == "cpu_cores"
    assert ot.data_properties[1].type == "string"


def test_object_type_get_empty_data_properties(capture: RequestCapture):
    """get() with no data_properties should return empty list."""
    def handler(req):
        return httpx.Response(200, json={
            "id": "ot-1", "name": "Pod", "kn_id": "kn-1",
        })
    client = make_client(handler, capture)
    ot = client.object_types.get("kn-1", "ot-1")
    assert ot.data_properties == []
