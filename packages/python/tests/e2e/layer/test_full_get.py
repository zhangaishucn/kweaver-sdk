"""E2E: Deep get — full property parsing."""
import pytest
from kweaver import KWeaverClient

pytestmark = pytest.mark.e2e


def test_object_type_get_data_properties(kweaver_client: KWeaverClient, kn_with_data):
    """SDK: get() returns data_properties from real API."""
    kn = kn_with_data["kn"]
    ot = kn_with_data["ot"]
    result = kweaver_client.object_types.get(kn.id, ot.id)
    # data_properties should be parsed (may be empty if OT has none)
    assert isinstance(result.data_properties, list)
