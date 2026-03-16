"""Tests for relation_types resource."""

import httpx

from tests.conftest import RequestCapture, make_client

_RT_RESPONSE = {
    "id": "rt_01",
    "name": "产品_库存",
    "source_object_type_id": "ot_01",
    "target_object_type_id": "ot_02",
    "type": "direct",
}


def test_direct_mapping(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [_RT_RESPONSE]})

    client = make_client(handler, capture)
    rt = client.relation_types.create(
        "kn_01",
        name="产品_库存",
        source_ot_id="ot_01",
        target_ot_id="ot_02",
        mappings=[("material_number", "material_code")],
    )

    body = capture.last_body()
    entry = body["entries"][0]
    assert entry["type"] == "direct"
    assert entry["mapping_rules"][0]["source_property"]["name"] == "material_number"
    assert entry["mapping_rules"][0]["target_property"]["name"] == "material_code"
    assert rt.mapping_type == "direct"


def test_dataview_mapping(capture: RequestCapture):
    resp = {**_RT_RESPONSE, "type": "data_view"}

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [resp]})

    client = make_client(handler, capture)
    rt = client.relation_types.create(
        "kn_01",
        name="产品_供应商",
        source_ot_id="ot_01",
        target_ot_id="ot_03",
        mapping_view_id="dv_bridge",
        source_mappings=[("product_id", "prod_id")],
        target_mappings=[("supplier_id", "sup_id")],
    )

    body = capture.last_body()
    entry = body["entries"][0]
    assert entry["type"] == "data_view"
    rules = entry["mapping_rules"]
    assert rules["backing_data_source"]["id"] == "dv_bridge"
    assert rules["source_mapping_rules"][0]["source_property"]["name"] == "product_id"
    assert rules["target_mapping_rules"][0]["target_property"]["name"] == "sup_id"
    assert rt.mapping_type == "data_view"
