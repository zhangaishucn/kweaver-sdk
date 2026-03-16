"""KWeaver SDK — CLI and client library for KWeaver knowledge networks."""

from kweaver._auth import ConfigAuth, OAuth2Auth, OAuth2BrowserAuth, PasswordAuth, TokenAuth
from kweaver._client import KWeaverClient
from kweaver._errors import (
    KWeaverError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NetworkError,
    NotFoundError,
    ServerError,
    ValidationError,
)

__all__ = [
    "KWeaverClient",
    "TokenAuth",
    "PasswordAuth",
    "OAuth2Auth",
    "ConfigAuth",
    "OAuth2BrowserAuth",
    "KWeaverError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "NetworkError",
    "NotFoundError",
    "ServerError",
    "ValidationError",
]
