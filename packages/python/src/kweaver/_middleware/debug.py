"""Debug middleware — prints full request/response diagnostics to stderr."""
from __future__ import annotations

import json
import sys
import time
from typing import Any

from kweaver._middleware import RequestContext, RequestHandler


def _mask_auth(headers: dict[str, str]) -> dict[str, str]:
    """Mask Authorization header value."""
    out = dict(headers)
    for key in list(out):
        if key.lower() == "authorization":
            val = out[key]
            if len(val) > 20:
                out[key] = val[:10] + "***"
            else:
                out[key] = "***"
    return out


class DebugMiddleware:
    """Print full request/response diagnostics + curl command to stderr."""

    def wrap(self, handler: RequestHandler) -> RequestHandler:
        def wrapper(ctx: RequestContext) -> Any:
            headers = ctx.kwargs.get("headers") or {}
            body = ctx.kwargs.get("json") or ctx.kwargs.get("data")

            # Request
            print(f"\n──── REQUEST ────────────────────────────────────", file=sys.stderr)
            print(f"{ctx.method} {ctx.path}", file=sys.stderr)
            if headers:
                print("Headers:", file=sys.stderr)
                for k, v in _mask_auth(headers).items():
                    print(f"  {k}: {v}", file=sys.stderr)
            if body:
                body_str = json.dumps(body, indent=2, ensure_ascii=False, default=str)
                if len(body_str) > 4096:
                    body_str = body_str[:4096] + "\n  ... (truncated)"
                print(f"Body:\n  {body_str}", file=sys.stderr)

            # Execute
            start = time.monotonic()
            result = handler(ctx)
            elapsed_ms = (time.monotonic() - start) * 1000

            # Response
            print(f"\n──── RESPONSE ({elapsed_ms:.1f}ms) ───────────────────", file=sys.stderr)
            if isinstance(result, dict):
                resp_str = json.dumps(result, indent=2, ensure_ascii=False, default=str)
                if len(resp_str) > 4096:
                    resp_str = resp_str[:4096] + "\n  ... (truncated)"
                print(resp_str, file=sys.stderr)

            # Curl equivalent
            print(f"\n──── CURL ──────────────────────────────────────", file=sys.stderr)
            curl_parts = [f"curl -X {ctx.method} '{ctx.path}'"]
            for k, v in _mask_auth(headers).items():
                curl_parts.append(f"  -H '{k}: {v}'")
            if body:
                curl_parts.append(f"  -d '{json.dumps(body, ensure_ascii=False, default=str)}'")
            print(" \\\n".join(curl_parts), file=sys.stderr)

            return result
        return wrapper
