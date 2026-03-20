"""E2E: BKN inspect composite method."""
import pytest
from kweaver import KWeaverClient
from kweaver.types import BKNInspectReport

pytestmark = pytest.mark.e2e


def test_inspect(kweaver_client: KWeaverClient, kn_with_data):
    """SDK: inspect returns aggregated report."""
    kn = kn_with_data["kn"]
    report = kweaver_client.knowledge_networks.inspect(kn.id)
    assert isinstance(report, BKNInspectReport)
    assert report.kn.id == kn.id
    assert report.stats.object_types_total >= 0
