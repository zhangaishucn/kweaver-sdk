"""Tests for DryRun middleware."""
from __future__ import annotations

import pytest
from kweaver._errors import DryRunIntercepted, KWeaverError


def test_dry_run_intercepted_is_kweaver_error():
    exc = DryRunIntercepted(method="POST", url="/api/test", body={"name": "foo"})
    assert isinstance(exc, KWeaverError)
    assert exc.method == "POST"
    assert exc.url == "/api/test"
    assert exc.body == {"name": "foo"}
    assert "[DRY RUN]" in str(exc)


def test_dry_run_intercepted_no_body():
    exc = DryRunIntercepted(method="DELETE", url="/api/test/1")
    assert exc.body is None
    assert "DELETE" in str(exc)


from kweaver._middleware import RequestContext
from kweaver._middleware.dry_run import DryRunMiddleware


def test_dry_run_passes_get():
    """GET requests should pass through normally."""
    def handler(ctx: RequestContext) -> dict:
        return {"data": "ok"}
    mw = DryRunMiddleware()
    wrapped = mw.wrap(handler)
    ctx = RequestContext(method="GET", path="/api/test", kwargs={})
    assert wrapped(ctx) == {"data": "ok"}


def test_dry_run_passes_head():
    """HEAD requests should pass through."""
    mw = DryRunMiddleware()
    wrapped = mw.wrap(lambda ctx: {"ok": True})
    ctx = RequestContext(method="HEAD", path="/api/test", kwargs={})
    assert wrapped(ctx) == {"ok": True}


def test_dry_run_intercepts_post():
    """POST should raise DryRunIntercepted."""
    mw = DryRunMiddleware()
    wrapped = mw.wrap(lambda ctx: {"should": "not reach"})
    ctx = RequestContext(method="POST", path="/api/objects", kwargs={"json": {"name": "Pod"}})
    with pytest.raises(DryRunIntercepted) as exc_info:
        wrapped(ctx)
    assert exc_info.value.method == "POST"
    assert exc_info.value.body == {"name": "Pod"}


def test_dry_run_intercepts_put():
    mw = DryRunMiddleware()
    wrapped = mw.wrap(lambda ctx: None)
    ctx = RequestContext(method="PUT", path="/api/objects/1", kwargs={"json": {"name": "new"}})
    with pytest.raises(DryRunIntercepted):
        wrapped(ctx)


def test_dry_run_intercepts_delete():
    mw = DryRunMiddleware()
    wrapped = mw.wrap(lambda ctx: None)
    ctx = RequestContext(method="DELETE", path="/api/objects/1", kwargs={})
    with pytest.raises(DryRunIntercepted):
        wrapped(ctx)


def test_dry_run_intercepts_patch():
    mw = DryRunMiddleware()
    wrapped = mw.wrap(lambda ctx: None)
    ctx = RequestContext(method="PATCH", path="/api/objects/1", kwargs={"json": {"name": "upd"}})
    with pytest.raises(DryRunIntercepted):
        wrapped(ctx)
