"""Parse Next.js __NEXT_DATA__ from /oauth2/signin HTML (1:1 with TS parseSigninPageHtmlProps)."""
from __future__ import annotations

import base64
import json
import re
from typing import Any, TypedDict

from cryptography.hazmat.primitives.serialization import load_der_public_key

_NEXT_DATA_RE = re.compile(
    r'<script[^>]*\bid=["\']__NEXT_DATA__["\'][^>]*>([\s\S]*?)</script>',
    re.IGNORECASE,
)
_HTML_MODULUS_RE = re.compile(r'"modulus"\s*:\s*"([0-9a-fA-F]{200,})"')
_HTML_PUBKEY_RE = re.compile(r'"(?:publicKey|rsaPublicKey|encryptPublicKey)"\s*:\s*"([A-Za-z0-9+/=]{200,})"')

# Order matches TS extractRsaPublicKeyMaterialFromPageProps (oauth.ts).
_PAGEPROP_RSA_KEYS = (
    "publicKey",
    "rsaPublicKey",
    "public_key",
    "modulus",
    "encryptPublicKey",
    "pubKey",
    "rsaModulus",
    "passwordPublicKey",
    "loginPublicKey",
    "encryptKey",
    "pwdPublicKey",
    "modulusHex",
    "rsaPublicKeyHex",
)


class SigninPageProps(TypedDict, total=False):
    challenge: str | None
    csrftoken: str
    remember: bool | None
    rsa_public_key_material: str | None


def _try_der_spki_base64_to_pem(material: str) -> str | None:
    """Same gate as TS tryDerSpkiBase64ToPem — returns non-None iff DER parses as SPKI RSA public key."""
    trimmed = re.sub(r"\s+", "", material)
    if len(trimmed) < 80 or not re.fullmatch(r"[A-Za-z0-9+/]+=*", trimmed):
        return None
    try:
        buf = base64.b64decode(trimmed, validate=False)
        load_der_public_key(buf)
    except Exception:
        return None
    return trimmed


def _is_likely_rsa_hex_modulus_string(s: str) -> bool:
    h = re.sub(r"\s+", "", s)
    return bool(len(h) >= 128 and len(h) % 2 == 0 and re.fullmatch(r"[0-9a-fA-F]+", h))


def _is_likely_spki_base64_string(s: str) -> bool:
    t = re.sub(r"\s+", "", s)
    if len(t) < 200 or not re.fullmatch(r"[A-Za-z0-9+/]+=*", t):
        return False
    return _try_der_spki_base64_to_pem(s) is not None


def _classify_signin_rsa_string(obj: str) -> str | None:
    """TS deepFindSigninRsaMaterial branch for typeof string."""
    t = obj.strip()
    if not t:
        return None
    if "BEGIN PUBLIC KEY" in t or "BEGIN RSA PUBLIC KEY" in t:
        return t
    if _is_likely_rsa_hex_modulus_string(t):
        return re.sub(r"\s+", "", t)
    if _is_likely_spki_base64_string(t):
        return re.sub(r"\s+", "", t)
    return None


def _deep_find_signin_rsa_material(obj: Any, depth: int, seen: set[int]) -> str | None:
    """TS deepFindSigninRsaMaterial — depth counts down per recursion."""
    if depth < 0 or obj is None:
        return None
    if isinstance(obj, str):
        return _classify_signin_rsa_string(obj)
    if not isinstance(obj, (dict, list)):
        return None
    oid = id(obj)
    if oid in seen:
        return None
    seen.add(oid)
    if isinstance(obj, list):
        for el in obj:
            r = _deep_find_signin_rsa_material(el, depth - 1, seen)
            if r:
                return r
        return None
    rec = obj
    for _k, v in rec.items():
        r = _deep_find_signin_rsa_material(v, depth - 1, seen)
        if r:
            return r
    return None


def _extract_rsa_public_key_material_from_page_props(pp: dict) -> str | None:
    """TS extractRsaPublicKeyMaterialFromPageProps."""
    for k in _PAGEPROP_RSA_KEYS:
        v = pp.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return _deep_find_signin_rsa_material(pp, 5, set())


def _html_regex_fallback(html: str) -> str | None:
    m = _HTML_MODULUS_RE.search(html)
    if m:
        return m.group(1)
    m = _HTML_PUBKEY_RE.search(html)
    if m:
        return m.group(1)
    return None


def parse_signin_page_html_props(html: str) -> SigninPageProps:
    """Parse Next.js __NEXT_DATA__ from the OAuth2 sign-in HTML shell.

    Returns a dict with: challenge, csrftoken, remember, rsa_public_key_material.
    Raises RuntimeError when __NEXT_DATA__ or csrftoken is absent.
    """
    m = _NEXT_DATA_RE.search(html)
    if not m:
        raise RuntimeError("Could not find __NEXT_DATA__ on the sign-in page.")
    data = json.loads(m.group(1))
    page_props = (data.get("props") or {}).get("pageProps")
    if not isinstance(page_props, dict):
        raise RuntimeError("Invalid __NEXT_DATA__: missing pageProps.")
    csrftoken = page_props.get("csrftoken") or page_props.get("_csrf")
    if not isinstance(csrftoken, str):
        raise RuntimeError(
            "Sign-in page did not expose csrftoken (expected in __NEXT_DATA__.props.pageProps)."
        )
    challenge = page_props.get("challenge")
    challenge_str = challenge if isinstance(challenge, str) else None
    remember_raw = page_props.get("remember")
    if isinstance(remember_raw, bool):
        remember: bool | None = remember_raw
    elif isinstance(remember_raw, str):
        remember = remember_raw == "true"
    else:
        remember = None
    material = _extract_rsa_public_key_material_from_page_props(page_props)
    if not material:
        material = _deep_find_signin_rsa_material(data, 10, set())
    if not material:
        material = _html_regex_fallback(html)
    return {
        "challenge": challenge_str,
        "csrftoken": csrftoken,
        "remember": remember,
        "rsa_public_key_material": material,
    }
