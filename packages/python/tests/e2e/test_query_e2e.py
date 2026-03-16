"""E2E: query operations — semantic search, instance query, subgraph.

Requires at least one built knowledge network with indexed data.
Read-only tests (non-destructive).
"""

from __future__ import annotations

import pytest

from kweaver import KWeaverClient
from kweaver.types import Condition

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def kn_with_data(kweaver_client: KWeaverClient):
    """Find a KN with at least one object type that has indexed data.

    Prefer a smaller object type (by doc_count) to avoid server-side
    timeouts on very large tables.
    """
    kns = kweaver_client.knowledge_networks.list()
    candidates: list[tuple] = []
    for kn in kns:
        ots = kweaver_client.object_types.list(kn.id)
        for ot in ots:
            if ot.status and ot.status.doc_count > 0:
                candidates.append((kn, ot))
    if not candidates:
        pytest.skip("No knowledge network with indexed data found")
    # Pick the object type with the smallest doc_count
    kn, ot = min(candidates, key=lambda x: x[1].status.doc_count)
    return {"kn": kn, "ot": ot}


def test_semantic_search(kweaver_client: KWeaverClient, kn_with_data):
    """Semantic search should return concepts."""
    kn = kn_with_data["kn"]
    result = kweaver_client.query.semantic_search(
        kn_id=kn.id, query=kn_with_data["ot"].name,
    )
    assert result is not None
    assert isinstance(result.concepts, list)


def test_instance_query(kweaver_client: KWeaverClient, kn_with_data):
    """Instance query should return data rows."""
    kn = kn_with_data["kn"]
    ot = kn_with_data["ot"]
    result = kweaver_client.query.instances(kn.id, ot.id, limit=5)

    assert isinstance(result.data, list)
    assert result.total_count is not None
    assert result.total_count > 0


def test_instance_query_with_pagination(kweaver_client: KWeaverClient, kn_with_data):
    """Instance query should support cursor-based pagination."""
    kn = kn_with_data["kn"]
    ot = kn_with_data["ot"]

    page1 = kweaver_client.query.instances(kn.id, ot.id, limit=2)
    if page1.search_after is None:
        pytest.skip("Not enough data for pagination test")

    page2 = kweaver_client.query.instances(
        kn.id, ot.id, limit=2, search_after=page1.search_after,
    )
    assert isinstance(page2.data, list)
    # Pages should not overlap (if enough data)
    if page1.data and page2.data:
        assert page1.data != page2.data


def test_instance_iter(kweaver_client: KWeaverClient, kn_with_data):
    """instances_iter should yield multiple pages."""
    kn = kn_with_data["kn"]
    ot = kn_with_data["ot"]

    pages = []
    for page in kweaver_client.query.instances_iter(kn.id, ot.id, limit=2):
        pages.append(page)
        if len(pages) >= 3:
            break

    assert len(pages) >= 1
    assert all(isinstance(p.data, list) for p in pages)
