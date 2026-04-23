"""Public auth API. Re-exports grow incrementally per task."""
from __future__ import annotations

from kweaver.auth._crypto import (
    DEFAULT_SIGNIN_RSA_MODULUS_HEX,
    STUDIOWEB_LOGIN_PUBLIC_KEY_PEM,
    encrypt_pkcs1_v15,
    rsa_modulus_hex_to_spki_pem,
)
from kweaver.auth._signin_html import parse_signin_page_html_props

__all__ = [
    "DEFAULT_SIGNIN_RSA_MODULUS_HEX",
    "STUDIOWEB_LOGIN_PUBLIC_KEY_PEM",
    "encrypt_pkcs1_v15",
    "rsa_modulus_hex_to_spki_pem",
    "parse_signin_page_html_props",
]
