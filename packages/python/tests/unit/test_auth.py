"""Tests for authentication providers."""

from kweaver._auth import TokenAuth


def test_token_auth_headers():
    auth = TokenAuth("Bearer eyJ...")
    headers = auth.auth_headers()
    assert headers["Authorization"] == "Bearer eyJ..."


def test_token_auth_repr_hides_token():
    auth = TokenAuth("Bearer secret-token")
    assert "secret-token" not in repr(auth)
    assert "***" in repr(auth)
