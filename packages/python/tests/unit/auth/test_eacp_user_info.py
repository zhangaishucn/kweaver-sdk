"""Tests for fetch_eacp_user_info + InitialPasswordChangeRequiredError shape."""
from __future__ import annotations

import httpx
import respx

from kweaver.auth.eacp import (
    InitialPasswordChangeRequiredError,
    fetch_eacp_user_info,
)


@respx.mock
def test_fetch_eacp_user_info_ok() -> None:
    respx.get("https://example.com/api/eacp/v1/user/get").mock(
        return_value=httpx.Response(200, json={"id": "u1", "account": "alice", "type": "user"})
    )
    info = fetch_eacp_user_info("https://example.com", access_token="tok")
    assert info is not None
    assert info["id"] == "u1"
    assert info["account"] == "alice"


@respx.mock
def test_fetch_eacp_user_info_returns_none_on_4xx() -> None:
    respx.get("https://example.com/api/eacp/v1/user/get").mock(
        return_value=httpx.Response(401, json={"code": 1})
    )
    assert fetch_eacp_user_info("https://example.com", access_token="tok") is None


def test_initial_password_change_required_error_fields() -> None:
    err = InitialPasswordChangeRequiredError(
        account="alice", base_url="https://x", server_message="must change"
    )
    assert err.code == 401001017
    assert err.http_status == 401
    assert err.account == "alice"
    assert err.base_url == "https://x"
    assert err.server_message == "must change"
    assert "must change" in str(err)
