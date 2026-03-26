"""Tests for dataflows resource."""

import time
from unittest.mock import patch

import httpx
import pytest

from kweaver._errors import KWeaverError
from kweaver.resources.dataflows import DataflowResult, DataflowStep
from tests.conftest import RequestCapture, make_client


# ── Helpers ──────────────────────────────────────────────────────────────────

SAMPLE_STEPS = [
    DataflowStep(id="s1", title="Import CSV", operator="csv_import", parameters={"file": "a.csv"}),
]

SAMPLE_DICT_STEPS = [
    {"id": "s1", "title": "Import CSV", "operator": "csv_import", "parameters": {"file": "a.csv"}},
]


# ── create ───────────────────────────────────────────────────────────────────


def test_create_returns_dag_id(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "dag_001"})

    client = make_client(handler, capture)
    dag_id = client.dataflows.create(title="test", steps=SAMPLE_STEPS)

    assert dag_id == "dag_001"
    body = capture.last_body()
    assert body["title"] == "test"
    assert body["trigger_config"] == {"operator": "manual"}
    assert len(body["steps"]) == 1
    assert body["steps"][0]["operator"] == "csv_import"


def test_create_with_dict_steps(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "dag_002"})

    client = make_client(handler, capture)
    dag_id = client.dataflows.create(title="dict-test", steps=SAMPLE_DICT_STEPS)

    assert dag_id == "dag_002"
    body = capture.last_body()
    assert body["steps"][0]["id"] == "s1"


def test_create_with_description(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "dag_003"})

    client = make_client(handler, capture)
    client.dataflows.create(title="t", steps=SAMPLE_DICT_STEPS, description="my desc")

    body = capture.last_body()
    assert body["description"] == "my desc"


def test_create_without_description(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "dag_004"})

    client = make_client(handler, capture)
    client.dataflows.create(title="t", steps=SAMPLE_DICT_STEPS)

    body = capture.last_body()
    assert "description" not in body


# ── run ──────────────────────────────────────────────────────────────────────


def test_run_posts_empty_body(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = make_client(handler, capture)
    client.dataflows.run("dag_001")

    url = capture.last_url()
    assert "/run-instance/dag_001" in url
    assert capture.last_body() == {}


# ── poll ─────────────────────────────────────────────────────────────────────


def test_poll_returns_on_success(capture: RequestCapture):
    call_count = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(200, json={"results": []})
        return httpx.Response(200, json={"results": [{"status": "success"}]})

    client = make_client(handler, capture)
    with patch("kweaver.resources.dataflows.time.sleep"):
        result = client.dataflows.poll("dag_001", interval=0.01)

    assert result.status == "success"
    assert call_count == 3


def test_poll_returns_on_completed(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"status": "completed"}]})

    client = make_client(handler, capture)
    result = client.dataflows.poll("dag_001")

    assert result.status == "completed"


def test_poll_raises_on_failed(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"status": "failed", "reason": "bad data"}]})

    client = make_client(handler, capture)

    with pytest.raises(KWeaverError, match="bad data"):
        client.dataflows.poll("dag_001")


def test_poll_raises_on_error_status(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"status": "error"}]})

    client = make_client(handler, capture)

    with pytest.raises(KWeaverError, match="Dataflow run error"):
        client.dataflows.poll("dag_001")


def test_poll_timeout(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    client = make_client(handler, capture)

    with patch("kweaver.resources.dataflows.time.sleep"):
        with patch("kweaver.resources.dataflows.time.monotonic") as mock_mono:
            # First call: start time. Second+: past deadline.
            mock_mono.side_effect = [0.0, 100.0, 100.0]
            with pytest.raises(TimeoutError, match="timed out"):
                client.dataflows.poll("dag_001", timeout=5.0)


# ── delete ───────────────────────────────────────────────────────────────────


def test_delete_sends_request(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    client = make_client(handler, capture)
    client.dataflows.delete("dag_001")

    url = capture.last_url()
    assert "/data-flow/flow/dag_001" in url


def test_delete_swallows_errors(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "internal"})

    client = make_client(handler, capture)
    # Should not raise
    client.dataflows.delete("dag_001")


# ── execute ──────────────────────────────────────────────────────────────────


def test_execute_full_lifecycle(capture: RequestCapture):
    call_count = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        url = str(req.url)
        if req.method == "POST" and "data-flow/flow" in url and "run-instance" not in url:
            return httpx.Response(200, json={"id": "dag_exec"})
        if req.method == "POST" and "run-instance" in url:
            return httpx.Response(200, json={})
        if req.method == "GET" and "results" in url:
            return httpx.Response(200, json={"results": [{"status": "success"}]})
        if req.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(404)

    client = make_client(handler, capture)
    with patch("kweaver.resources.dataflows.time.sleep"):
        result = client.dataflows.execute(title="e2e", steps=SAMPLE_STEPS)

    assert result.status == "success"
    # Verify all 4 stages were called: create, run, poll, delete
    methods = [r.method for r in capture.requests]
    assert methods.count("POST") == 2  # create + run
    assert methods.count("GET") == 1   # poll
    assert methods.count("DELETE") == 1  # delete


def test_execute_deletes_on_poll_failure(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if req.method == "POST" and "data-flow/flow" in url and "run-instance" not in url:
            return httpx.Response(200, json={"id": "dag_fail"})
        if req.method == "POST" and "run-instance" in url:
            return httpx.Response(200, json={})
        if req.method == "GET" and "results" in url:
            return httpx.Response(200, json={"results": [{"status": "failed", "reason": "oops"}]})
        if req.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(404)

    client = make_client(handler, capture)

    with pytest.raises(KWeaverError, match="oops"):
        with patch("kweaver.resources.dataflows.time.sleep"):
            client.dataflows.execute(title="fail", steps=SAMPLE_STEPS)

    # Delete should still be called (finally block)
    methods = [r.method for r in capture.requests]
    assert "DELETE" in methods


# ── DataflowStep / DataflowResult ────────────────────────────────────────────


def test_dataflow_step_defaults():
    step = DataflowStep(id="x", title="y", operator="z")
    assert step.parameters == {}


def test_dataflow_result_defaults():
    result = DataflowResult(status="success")
    assert result.reason is None


def test_poll_uses_exponential_backoff(capture: RequestCapture):
    """Poll should use exponential backoff instead of fixed interval."""
    call_count = 0

    def handler(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 5:
            return httpx.Response(200, json={"results": []})
        return httpx.Response(200, json={"results": [{"status": "success"}]})

    client = make_client(handler, capture)
    sleep_calls = []
    with patch("kweaver.resources.dataflows.time.sleep", side_effect=lambda s: sleep_calls.append(s)):
        with patch("kweaver.resources.dataflows.time.monotonic") as mock_mono:
            mock_mono.return_value = 0.0
            result = client.dataflows.poll("dag_001", interval=3.0, timeout=900.0)

    assert result.status == "success"
    # Backoff: 3, 6, 12, 24 (doubling from initial interval, capped at 30)
    assert sleep_calls == [3.0, 6.0, 12.0, 24.0]
