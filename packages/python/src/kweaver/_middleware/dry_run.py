"""DryRun middleware — intercepts write operations."""
from __future__ import annotations

from typing import Any

from kweaver._errors import DryRunIntercepted
from kweaver._middleware import RequestContext, RequestHandler

_READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class DryRunMiddleware:
    """Intercept write requests (POST/PUT/DELETE/PATCH), let reads pass through."""

    def wrap(self, handler: RequestHandler) -> RequestHandler:
        def wrapper(ctx: RequestContext) -> Any:
            if ctx.method.upper() in _READ_METHODS:
                return handler(ctx)
            body = ctx.kwargs.get("json") or ctx.kwargs.get("data")
            raise DryRunIntercepted(method=ctx.method, url=ctx.path, body=body)
        return wrapper
