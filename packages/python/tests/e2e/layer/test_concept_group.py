"""E2E: Concept group read operations."""
import pytest
from kweaver import KWeaverClient

pytestmark = pytest.mark.e2e


def test_concept_group_list(kweaver_client: KWeaverClient, kn_with_data):
    """SDK: list concept groups (may be empty)."""
    kn = kn_with_data["kn"]
    cgs = kweaver_client.concept_groups.list(kn.id)
    assert isinstance(cgs, list)


def test_concept_group_get_if_exists(kweaver_client: KWeaverClient, kn_with_data):
    """SDK: get concept group if any exist."""
    kn = kn_with_data["kn"]
    cgs = kweaver_client.concept_groups.list(kn.id)
    if not cgs:
        pytest.skip("No concept groups exist")
    cg = kweaver_client.concept_groups.get(kn.id, cgs[0].id)
    assert cg.id == cgs[0].id
