"""Tests for KN inspect() composite method."""
import httpx
from tests.conftest import make_client
from kweaver.types import BKNInspectReport


def test_inspect_returns_report():
    """inspect() should aggregate KN info + stats + jobs."""
    def handler(req):
        url = str(req.url)
        if req.method == "GET" and "/kn-1" in url and "jobs" not in url:
            return httpx.Response(200, json={
                "id": "kn-1", "name": "k8s", "tags": [],
                "statistics": {
                    "object_types_total": 3,
                    "relation_types_total": 1,
                    "action_types_total": 0,
                    "concept_groups_total": 1,
                },
            })
        if "jobs" in url:
            return httpx.Response(200, json={"entries": []})
        return httpx.Response(200, json={})

    client = make_client(handler)
    report = client.knowledge_networks.inspect("kn-1")
    assert isinstance(report, BKNInspectReport)
    assert report.kn.id == "kn-1"
    assert report.stats.object_types_total == 3
    assert report.active_jobs == []


def test_inspect_partial_failure():
    """inspect() should return partial results when jobs endpoint fails."""
    def handler(req):
        url = str(req.url)
        if "/kn-1" in url and "jobs" not in url:
            return httpx.Response(200, json={
                "id": "kn-1", "name": "k8s", "tags": [],
                "statistics": {"object_types_total": 2, "relation_types_total": 0,
                               "action_types_total": 0, "concept_groups_total": 0},
            })
        if "jobs" in url:
            return httpx.Response(500, json={"error": "internal"})
        return httpx.Response(200, json={})

    client = make_client(handler)
    report = client.knowledge_networks.inspect("kn-1")
    assert report.kn.id == "kn-1"
    assert report.active_jobs == []  # failed gracefully
