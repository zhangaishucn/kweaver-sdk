"""Tests for dataviews resource."""

import json

import httpx
import pytest

from tests.conftest import RequestCapture, make_client


def test_create_table_mode_finds_atomic_view(capture: RequestCapture):
    """Table-based create should find the auto-created atomic view."""
    def handler(req: httpx.Request) -> httpx.Response:
        if req.method == "GET":
            return httpx.Response(200, json={
                "entries": [{
                    "id": "dv_01", "name": "products", "type": "atomic",
                    "query_type": "SQL", "fields": [],
                    "data_source_id": "ds_01",
                }],
            })
        return httpx.Response(200, json=[])

    client = make_client(handler, capture)
    dv = client.dataviews.create(name="products", datasource_id="ds_01", table="products")

    assert dv.id == "dv_01"
    assert dv.name == "products"
    assert capture.requests[-1].method == "GET"


def test_create_table_mode_creates_if_not_found(capture: RequestCapture):
    """When no atomic view exists, should create one directly."""
    def handler(req: httpx.Request) -> httpx.Response:
        if req.method == "GET":
            url = str(req.url)
            if "data-views?" in url:
                return httpx.Response(200, json={"entries": []})
            elif "data-views/" in url:
                return httpx.Response(200, json={
                    "id": "created_01", "name": "missing",
                    "query_type": "SQL", "type": "atomic",
                    "data_source_id": "ds_01", "fields": [],
                })
        if req.method == "POST":
            return httpx.Response(201, json=[{"id": "created_01"}])
        return httpx.Response(200, json=[])

    client = make_client(handler, capture)
    original = client.dataviews.find_by_table
    client.dataviews.find_by_table = lambda ds_id, name, **kw: original(ds_id, name, wait=False)

    dv = client.dataviews.create(name="missing", datasource_id="ds_01", table="missing")

    assert dv.id == "created_01"
    methods = [r.method for r in capture.requests]
    assert "POST" in methods


def test_create_sql_mode(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        if req.method == "POST":
            return httpx.Response(201, json=[{"id": "dv_02"}])
        return httpx.Response(200, json={
            "id": "dv_02", "name": "custom", "query_type": "SQL",
            "data_source_id": "ds_01", "fields": [],
        })

    client = make_client(handler, capture)
    client.dataviews.create(
        name="custom", datasource_id="ds_01",
        sql="SELECT id FROM products WHERE status = 'active'",
    )

    # Find the POST request
    post_reqs = [r for r in capture.requests if r.method == "POST"]
    assert post_reqs
    body = json.loads(post_reqs[-1].content)
    assert body[0]["type"] == "custom"
    assert body[0]["data_scope"][0]["type"] == "sql"
    assert "SELECT" in body[0]["data_scope"][0]["config"]["sql_expression"]


def test_create_requires_table_or_sql():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = make_client(handler)
    with pytest.raises(ValueError, match="Either"):
        client.dataviews.create(name="bad", datasource_id="ds_01")
