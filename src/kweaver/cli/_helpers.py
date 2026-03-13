"""Shared helpers for CLI commands."""

from __future__ import annotations

import json
import os
import sys
from functools import wraps
from typing import Any

import click

from kweaver._auth import ConfigAuth, PasswordAuth, TokenAuth
from kweaver._client import ADPClient
from kweaver._errors import ADPError, AuthenticationError, AuthorizationError, NotFoundError


def make_client() -> ADPClient:
    """Build an ADPClient from env vars or ~/.kweaver/ config.

    Priority:
      1. ADP_TOKEN + ADP_BASE_URL  → TokenAuth
      2. ADP_USERNAME + ADP_PASSWORD + ADP_BASE_URL  → PasswordAuth (browser OAuth2)
      3. ~/.kweaver/ config  → ConfigAuth
    """
    token = os.environ.get("ADP_TOKEN")
    base_url = os.environ.get("ADP_BASE_URL")
    bd = os.environ.get("ADP_BUSINESS_DOMAIN")

    if token and base_url:
        return ADPClient(base_url=base_url, auth=TokenAuth(token), business_domain=bd)

    username = os.environ.get("ADP_USERNAME")
    password = os.environ.get("ADP_PASSWORD")
    if username and password and base_url:
        auth = PasswordAuth(base_url=base_url, username=username, password=password)
        return ADPClient(base_url=base_url, auth=auth, business_domain=bd)

    # Default: ConfigAuth reads ~/.kweaver/
    auth = ConfigAuth()
    return ADPClient(auth=auth, business_domain=bd)


def pp(data: Any) -> None:
    """Pretty-print JSON data."""
    click.echo(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def error_exit(msg: str, code: int = 1) -> None:
    click.echo(f"Error: {msg}", err=True)
    sys.exit(code)


def handle_errors(fn):
    """Decorator: catch SDK errors and exit with a user-friendly message."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AuthenticationError as e:
            error_exit(f"认证失败: {e.message}")
        except AuthorizationError as e:
            error_exit(f"无权限: {e.message}")
        except NotFoundError as e:
            error_exit(f"未找到: {e.message}")
        except ADPError as e:
            error_exit(f"错误: {e.message}")
    return wrapper
