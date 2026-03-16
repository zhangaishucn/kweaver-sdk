"""Tests for error hierarchy and raise_for_status."""

import httpx
import pytest

from kweaver._errors import (
    KWeaverError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ServerError,
    ValidationError,
    raise_for_status,
)


def _response(status: int, body: dict | None = None) -> httpx.Response:
    return httpx.Response(
        status,
        json=body or {},
        request=httpx.Request("GET", "https://mock/test"),
    )


def test_200_no_error():
    raise_for_status(_response(200))


def test_401_raises_authentication_error():
    with pytest.raises(AuthenticationError) as exc:
        raise_for_status(_response(401, {"error_code": "TOKEN_EXPIRED", "message": "token expired"}))
    assert exc.value.error_code == "TOKEN_EXPIRED"
    assert exc.value.status_code == 401


def test_403_raises_authorization_error():
    with pytest.raises(AuthorizationError):
        raise_for_status(_response(403))


def test_404_raises_not_found_error():
    with pytest.raises(NotFoundError):
        raise_for_status(_response(404))


def test_400_raises_validation_error():
    with pytest.raises(ValidationError):
        raise_for_status(_response(400))


def test_409_raises_conflict_error():
    with pytest.raises(ConflictError):
        raise_for_status(_response(409))


def test_500_raises_server_error():
    with pytest.raises(ServerError) as exc:
        raise_for_status(_response(500, {"message": "internal error", "trace_id": "t123"}))
    assert exc.value.trace_id == "t123"


def test_unknown_4xx_raises_adp_error():
    with pytest.raises(KWeaverError):
        raise_for_status(_response(418))


def test_error_repr():
    e = KWeaverError("test", status_code=400, error_code="BAD", trace_id="t1")
    r = repr(e)
    assert "400" in r
    assert "BAD" in r
