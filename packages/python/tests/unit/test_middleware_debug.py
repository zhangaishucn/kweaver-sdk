"""Tests for Debug middleware."""
from __future__ import annotations

from kweaver._middleware import RequestContext
from kweaver._middleware.debug import DebugMiddleware


def test_debug_prints_request_line(capsys):
    """Should print method + path to stderr."""
    mw = DebugMiddleware()
    wrapped = mw.wrap(lambda ctx: {"ok": True})
    ctx = RequestContext(method="GET", path="/api/kn/list", kwargs={})
    wrapped(ctx)
    err = capsys.readouterr().err
    assert "GET" in err
    assert "/api/kn/list" in err


def test_debug_masks_authorization(capsys):
    """Authorization header value should be masked."""
    mw = DebugMiddleware()
    wrapped = mw.wrap(lambda ctx: {"ok": True})
    ctx = RequestContext(
        method="GET", path="/api/test",
        kwargs={"headers": {"Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.longtoken"}}
    )
    wrapped(ctx)
    err = capsys.readouterr().err
    assert "eyJhbGciOiJSUzI1NiJ9.longtoken" not in err
    assert "***" in err


def test_debug_shows_timing(capsys):
    """Should include response timing."""
    mw = DebugMiddleware()
    wrapped = mw.wrap(lambda ctx: {"ok": True})
    ctx = RequestContext(method="GET", path="/api/test", kwargs={})
    wrapped(ctx)
    err = capsys.readouterr().err
    assert "RESPONSE" in err
    assert "ms" in err.lower()


def test_debug_generates_curl(capsys):
    """Should output a curl equivalent command."""
    mw = DebugMiddleware()
    wrapped = mw.wrap(lambda ctx: {"ok": True})
    ctx = RequestContext(
        method="POST", path="/api/test",
        kwargs={"json": {"name": "foo"}, "headers": {"Authorization": "Bearer tok123"}}
    )
    wrapped(ctx)
    err = capsys.readouterr().err
    assert "curl" in err.lower() or "CURL" in err
    assert "POST" in err
