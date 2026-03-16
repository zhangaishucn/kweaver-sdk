"""RSA password encryption for the KWeaver data-connection API.

The KWeaver backend requires datasource passwords to be RSA-encrypted
(PKCS1v15) using a platform-wide public key before transmission.
"""

from __future__ import annotations

import base64

# 2048-bit RSA public key shipped with the KWeaver platform.
_KWEAVER_PUBLIC_KEY_PEM = b"""\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA22GOSQ1jeDhpdzxhJddS
f+U10F4Ivut7giYhchFAIJgRonMamDT86MSqQUc8DdTFdPGLm7M3GUKcsG1qbC3S
qk4XJ9NjmQXbs7IMWyWEWQrN7Iv7S2QjDYJI+ppvIN03I0Km3WKsmnrle2bLzT/V
G8e72YX69dfXAeiX6uDhht1va/JxZVFMIV3pHa6AQQ9gn5SAUTX2akEhRfe1bPJj
fVyoM+dfNtvgdfaraqV1rOhVDEqd0NlOWt2RHwETQwU8gIJib2baj2MtyIAY+fQw
KlKWxUs1GcFbECnhVPiVN6BEhXD7OhRt9QE/cuYl5v4a6ypugGaMBK6VKOqFHDvf
mwIDAQAB
-----END PUBLIC KEY-----"""

_public_key = None


def _get_public_key():
    global _public_key
    if _public_key is None:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        _public_key = load_pem_public_key(_KWEAVER_PUBLIC_KEY_PEM)
    return _public_key


def encrypt_password(plaintext: str) -> str:
    """Encrypt a password with the KWeaver platform RSA public key.

    Returns a base64-encoded ciphertext string.
    """
    from cryptography.hazmat.primitives.asymmetric import padding

    key = _get_public_key()
    ciphertext = key.encrypt(plaintext.encode(), padding.PKCS1v15())
    return base64.b64encode(ciphertext).decode()
