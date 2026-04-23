"""Tests for _signin_html.parse_signin_page_html_props.

Mirror of packages/typescript/test/oauth-signin-html.test.ts — keep these
test names in lock-step with the TS suite for parity audits.
"""
from __future__ import annotations

import json

import pytest

from kweaver.auth._signin_html import parse_signin_page_html_props

SPKI_FIXTURE = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4E+eiWRwffhRIPQYvlXUjf0b3HqCmosi"
    "CxbFCYI/gdfDBhrTUzbt3fL3o/gRQQBEPf69vhJMFH2ZMtaJM6ohE3yQef331liPVM0YvqMOgvoI"
    "D+zDa1NIZFObSsjOKhvZtv9esO0REeiVEPKNc+Dp6il3x7TV9VKGEv0+iriNjqv7TGAexo2jVtLm"
    "50iVKTju2qmCDG83SnVHzsiNj70MiviqiLpgz72IxjF+xN4bRw8I5dD0GwwO8kDoJUGWgTds+Vck"
    "Cwdt"
    "ZA65oui9Osk5t1a4pg6Xu9+HFcEuqwJTDxATvGAz1/YW0oUisjM0ObKTRDVSfnTYeaBsN6L+M+8g"
    "CwIDAQAB"
)


def _wrap(data: dict) -> str:
    return (
        '<!DOCTYPE html><script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(data)
        + "</script>"
    )


def test_csrftoken_and_challenge() -> None:
    html = _wrap({"props": {"pageProps": {"challenge": "ch1", "csrftoken": "csrf1"}}})
    o = parse_signin_page_html_props(html)
    assert o["challenge"] == "ch1"
    assert o["csrftoken"] == "csrf1"
    assert o["remember"] is None


def test_accepts_underscore_csrf_instead_of_csrftoken() -> None:
    html = _wrap({"props": {"pageProps": {"challenge": "c", "_csrf": "x"}}})
    assert parse_signin_page_html_props(html)["csrftoken"] == "x"


def test_missing_next_data_throws() -> None:
    with pytest.raises(RuntimeError, match="__NEXT_DATA__"):
        parse_signin_page_html_props("<html></html>")


def test_missing_csrftoken_throws() -> None:
    html = _wrap({"props": {"pageProps": {"challenge": "c"}}})
    with pytest.raises(RuntimeError, match="csrftoken"):
        parse_signin_page_html_props(html)


def test_parses_remember_boolean() -> None:
    html = _wrap({"props": {"pageProps": {"challenge": "c", "csrftoken": "t", "remember": True}}})
    assert parse_signin_page_html_props(html)["remember"] is True


def test_parses_remember_string_true() -> None:
    html = _wrap({"props": {"pageProps": {"csrftoken": "t", "remember": "true"}}})
    assert parse_signin_page_html_props(html)["remember"] is True


def test_parses_public_key_hex_modulus_from_pageprops() -> None:
    html = _wrap({"props": {"pageProps": {"csrftoken": "t", "publicKey": "aabb"}}})
    assert parse_signin_page_html_props(html)["rsa_public_key_material"] == "aabb"


def test_finds_nested_base64_spki_in_pageprops() -> None:
    html = _wrap({
        "props": {"pageProps": {"csrftoken": "t", "auth": {"cfg": {"publicKey": SPKI_FIXTURE}}}}
    })
    assert parse_signin_page_html_props(html)["rsa_public_key_material"] == SPKI_FIXTURE


def test_regex_fallback_for_modulus_in_html() -> None:
    mod = "a" * 256
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps({"props": {"pageProps": {"csrftoken": "t"}}})
        + f'</script>extra "modulus":"{mod}"'
    )
    assert parse_signin_page_html_props(html)["rsa_public_key_material"] == mod


def test_rsa_material_under_props_outside_pageprops() -> None:
    html = _wrap({
        "props": {
            "pageProps": {"csrftoken": "t", "challenge": "c"},
            "extra": {"rsaPublicKey": SPKI_FIXTURE},
        }
    })
    assert parse_signin_page_html_props(html)["rsa_public_key_material"] == SPKI_FIXTURE
