"""Tests for datasources resource."""

import httpx

from tests.conftest import RequestCapture, make_client


def test_create_transforms_params(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "ds_01", "name": "测试库", "type": "mysql"})

    client = make_client(handler, capture)
    ds = client.datasources.create(
        name="测试库", type="mysql",
        host="10.0.1.100", port=3306,
        database="erp", account="root", password="secret",
    )

    body = capture.last_body()
    assert body["bin_data"]["host"] == "10.0.1.100"
    assert body["bin_data"]["database_name"] == "erp"
    assert body["bin_data"]["connect_protocol"] == "jdbc"
    # Password is RSA-encrypted before sending; verify it's not plaintext
    assert body["bin_data"]["password"] != "secret"
    assert len(body["bin_data"]["password"]) > 100  # RSA-2048 produces ~344 chars base64
    assert ds.id == "ds_01"


def test_create_maxcompute_uses_https(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "ds_02", "name": "mc", "type": "maxcompute"})

    client = make_client(handler, capture)
    client.datasources.create(
        name="mc", type="maxcompute",
        host="mc.example.com", port=443,
        database="proj", account="ak", password="sk",
    )
    body = capture.last_body()
    assert body["bin_data"]["connect_protocol"] == "https"


def test_test_connectivity(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = make_client(handler, capture)
    result = client.datasources.test(
        type="mysql", host="10.0.1.100", port=3306,
        database="erp", account="root", password="secret",
    )
    assert result is True
    assert "/datasource/test" in capture.last_url()


def test_list_tables(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "data": [
                {"name": "products", "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "varchar"},
                ]},
                {"name": "orders", "columns": []},
            ]
        })

    client = make_client(handler, capture)
    tables = client.datasources.list_tables("ds_01")
    assert len(tables) == 2
    assert tables[0].name == "products"
    assert tables[0].columns[0].name == "id"


def test_list_datasources():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [
            {"id": "ds_01", "name": "erp", "type": "mysql"},
        ]})

    client = make_client(handler)
    result = client.datasources.list(keyword="erp")
    assert len(result) == 1
    assert result[0].name == "erp"


def test_delete_datasource(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    client = make_client(handler, capture)
    client.datasources.delete("ds_01")
    assert "ds_01" in capture.last_url()
