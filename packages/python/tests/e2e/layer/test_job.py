"""E2E: Job read operations."""
import pytest
from kweaver import KWeaverClient

pytestmark = pytest.mark.e2e


def test_job_list(kweaver_client: KWeaverClient, kn_with_data):
    """SDK: list jobs (may be empty)."""
    kn = kn_with_data["kn"]
    jobs = kweaver_client.jobs.list(kn.id)
    assert isinstance(jobs, list)
