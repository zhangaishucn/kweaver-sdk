"""EACP authentication helpers (modify password, userinfo, initial-password error).

1:1 port of packages/typescript/src/auth/eacp-modify-password.ts +
the InitialPasswordChangeRequiredError class from auth/oauth.ts.
"""
from __future__ import annotations

import base64
from typing import Any, TypedDict

import httpx

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)

# 1024-bit RSA private key embedded in ShareServer's eachttpserver — same
# keypair the C++ binary ships to every customer for /auth1/modifypassword.
# Source: isf/ShareServer/.../ncEACHttpServerUtil.cpp::RSADecrypt.
EACP_MODIFYPWD_PRIVATE_KEY_PEM = """-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDB2fhLla9rMx+6LWTXajnK11Kdp520s1Q+TfPfIXI/7G9+L2YC
4RA3M5rgRi32s5+UFQ/CVqUFqMqVuzaZ4lw/uEdk1qHcP0g6LB3E9wkl2FclFR0M
+/HrWmxPoON+0y/tFQxxfNgsUodFzbdh0XY1rIVUIbPLvufUBbLKXHDPpwIDAQAB
AoGBALCM/H6ajXFs1nCR903aCVicUzoS9qckzI0SIhIOPCfMBp8+PAJTSJl9/ohU
YnhVj/kmVXwBvboxyJAmOcxdRPWL7iTk5nA1oiVXMer3Wby+tRg/ls91xQbJLVv3
oGSt7q0CXxJpRH2oYkVVlMMlZUwKz3ovHiLKAnhw+jEsdL2BAkEA9hA97yyeA2eq
f9dMu/ici99R3WJRRtk4NEI4WShtWPyziDg48d3SOzYmhEJjPuOo3g1ze01os70P
ApE7d0qcyQJBAMmt+FR8h5MwxPQPAzjh/fTuTttvUfBeMiUDrIycK1I/L96lH+fU
i4Nu+7TPOzExnPeGO5UJbZxrpIEUB7Zs8O8CQQCLzTCTGiNwxc5eMgH77kVrRudp
Q7nv6ex/7Hu9VDXEUFbkdyULbj9KuvppPJrMmWZROw04qgNp02mayM8jeLXZAkEA
o+PM/pMn9TPXiWE9xBbaMhUKXgXLd2KEq1GeAbHS/oY8l1hmYhV1vjwNLbSNrH9d
yEP73TQJL+jFiONHFTbYXwJAU03Xgum5mLIkX/02LpOrz2QCdfX1IMJk2iKi9osV
KqfbvHsF0+GvFGg18/FXStG9Kr4TjqLsygQJT76/MnMluw==
-----END RSA PRIVATE KEY-----"""

_cached_pub = None


def _embedded_public_key():
    global _cached_pub
    if _cached_pub is None:
        priv = load_pem_private_key(EACP_MODIFYPWD_PRIVATE_KEY_PEM.encode(), password=None)
        _cached_pub = priv.public_key()
    return _cached_pub


def encrypt_modify_pwd(plain: str, public_key_pem: str | None = None) -> str:
    """Encrypt with the EACP modifypassword RSA public key, base64-encoded."""
    key = (
        load_pem_public_key(public_key_pem.encode()) if public_key_pem else _embedded_public_key()
    )
    cipher = key.encrypt(plain.encode(), padding.PKCS1v15())
    return base64.b64encode(cipher).decode()


class EacpModifyPasswordResult(TypedDict, total=False):
    status: int
    ok: bool
    body: str
    json: Any


def eacp_modify_password(
    base_url: str,
    *,
    account: str,
    old_password: str,
    new_password: str,
    public_key_pem: str | None = None,
    tls_insecure: bool = False,
) -> EacpModifyPasswordResult:
    """Call EACP POST /api/eacp/v1/auth1/modifypassword (no bearer token required)."""
    body: dict[str, Any] = {
        "account": account,
        "oldpwd": encrypt_modify_pwd(old_password, public_key_pem),
        "newpwd": encrypt_modify_pwd(new_password, public_key_pem),
        "vcodeinfo": {"uuid": "", "vcode": ""},
        "isforgetpwd": False,
    }
    url = base_url.rstrip("/") + "/api/eacp/v1/auth1/modifypassword"
    resp = httpx.post(
        url,
        json=body,
        headers={"Accept": "application/json, text/plain, */*"},
        verify=not tls_insecure,
    )
    text = resp.text
    parsed: Any = None
    try:
        parsed = resp.json() if text else None
    except Exception:
        parsed = None
    return {"status": resp.status_code, "ok": resp.is_success, "body": text, "json": parsed}


def fetch_eacp_user_info(
    base_url: str, *, access_token: str, tls_insecure: bool = False
) -> dict[str, Any] | None:
    """Best-effort fetch of EACP userinfo. Returns None on non-200 / network error."""
    try:
        resp = httpx.get(
            base_url.rstrip("/") + "/api/eacp/v1/user/get",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            verify=not tls_insecure,
        )
        if resp.status_code != 200:
            return None
        info = resp.json()
        return info if isinstance(info, dict) else None
    except Exception:
        return None


class InitialPasswordChangeRequiredError(RuntimeError):
    """Raised on POST /oauth2/signin returning 401 with EACP code 401001017."""

    code: int = 401001017
    http_status: int = 401

    def __init__(self, *, account: str, base_url: str, server_message: str) -> None:
        super().__init__(server_message)
        self.account = account
        self.base_url = base_url
        self.server_message = server_message
