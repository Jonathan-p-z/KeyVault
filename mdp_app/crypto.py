from __future__ import annotations

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .config import (
    HEADER_V2,
    LEGACY_PBKDF2_ITERATIONS,
    LEGACY_SALT,
    MAGIC_V2,
    SCRYPT_N,
    SCRYPT_P,
    SCRYPT_R,
)


def generer_cle_legacy_pbkdf2(mdp: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=LEGACY_SALT,
        iterations=LEGACY_PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(mdp.encode("utf-8")))


def generer_cle_scrypt(mdp: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=n,
        r=r,
        p=p,
    )
    return base64.urlsafe_b64encode(kdf.derive(mdp.encode("utf-8")))


def encoder_v2(token: bytes, salt: bytes, n: int, r: int, p: int) -> bytes:
    return HEADER_V2.pack(MAGIC_V2, salt, n, r, p) + token


def decoder(data: bytes):
    if len(data) >= HEADER_V2.size and data[:4] == MAGIC_V2:
        magic, salt, n, r, p = HEADER_V2.unpack(data[: HEADER_V2.size])
        token = data[HEADER_V2.size :]
        return ("v2", salt, n, r, p, token)
    return ("legacy", None, None, None, None, data)


def dechiffrer_bytes(mdp: str, data: bytes) -> bytes:
    version, salt, n, r, p, token = decoder(data)
    if version == "v2":
        cle = generer_cle_scrypt(mdp, salt=salt, n=n, r=r, p=p)
        return Fernet(cle).decrypt(token)
    cle = generer_cle_legacy_pbkdf2(mdp)
    return Fernet(cle).decrypt(token)


def chiffrer_bytes_v2(mdp: str, contenu: bytes, *, salt: bytes) -> bytes:
    cle = generer_cle_scrypt(mdp, salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    token = Fernet(cle).encrypt(contenu)
    return encoder_v2(token=token, salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
