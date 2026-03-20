"""E2E: Observability middleware integration."""
import pytest
from kweaver import KWeaverClient

pytestmark = pytest.mark.e2e


def test_debug_does_not_break_requests(kweaver_client_factory, kn_with_data):
    """debug=True should not affect request/response correctness."""
    client = kweaver_client_factory(debug=True)
    kns = client.knowledge_networks.list()
    assert isinstance(kns, list)


def test_metrics_collector(kweaver_client_factory, kn_with_data):
    """metrics=True should accumulate request counts (placeholder -- not yet implemented)."""
    # TODO: enable when MetricsMiddleware is implemented in Infra Phase 2
    pass


def test_audit_log_written(tmp_path, kweaver_client_factory, kn_with_data):
    """audit_log should produce JSONL file (placeholder -- not yet implemented)."""
    # TODO: enable when AuditMiddleware is implemented in Infra Phase 2
    pass
