"""Tests for eacp_modify_password (POST /api/eacp/v1/auth1/modifypassword)."""
from __future__ import annotations

import base64
import json

import httpx
import respx

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from kweaver.auth.eacp import (
    EACP_MODIFYPWD_PRIVATE_KEY_PEM,
    eacp_modify_password,
    encrypt_modify_pwd,
)


def _decrypt(cipher_b64: str) -> str:
    priv = load_pem_private_key(EACP_MODIFYPWD_PRIVATE_KEY_PEM.encode(), password=None)
    return priv.decrypt(base64.b64decode(cipher_b64), padding.PKCS1v15()).decode()


def test_encrypt_modify_pwd_roundtrip_with_embedded_key() -> None:
    cipher = encrypt_modify_pwd("hunter2")
    assert _decrypt(cipher) == "hunter2"


@respx.mock
def test_eacp_modify_password_sends_encrypted_payload() -> None:
    captured = {}

    def _capture(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"code": 0})

    respx.post("https://example.com/api/eacp/v1/auth1/modifypassword").mock(side_effect=_capture)

    res = eacp_modify_password(
        "https://example.com/", account="alice", old_password="old", new_password="new"
    )
    assert res["status"] == 200
    assert captured["body"]["account"] == "alice"
    assert captured["body"]["isforgetpwd"] is False
    assert captured["body"]["vcodeinfo"] == {"uuid": "", "vcode": ""}
    assert _decrypt(captured["body"]["oldpwd"]) == "old"
    assert _decrypt(captured["body"]["newpwd"]) == "new"


@respx.mock
def test_eacp_modify_password_propagates_4xx() -> None:
    respx.post("https://example.com/api/eacp/v1/auth1/modifypassword").mock(
        return_value=httpx.Response(400, json={"code": 1, "message": "weak"})
    )
    res = eacp_modify_password(
        "https://example.com", account="a", old_password="o", new_password="n"
    )
    assert res["status"] == 400
    assert res["ok"] is False
    assert res["json"] == {"code": 1, "message": "weak"}
