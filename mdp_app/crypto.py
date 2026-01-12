from __future__ import annotations

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .config import (
    ARGON2_MEMORY_COST_KIB,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    HEADER_V2,
    LEGACY_PBKDF2_ITERATIONS,
    LEGACY_SALT,
    MAGIC_V2,
    MAGIC_V3,
    MAGIC_V4,
    SCRYPT_N,
    SCRYPT_P,
    SCRYPT_R,
)


def _encode_no_strings(data: bytes) -> bytes:
    """Encode bytes so that common `strings` output shows nothing.

    Each input byte becomes 2 bytes in range 0x80..0x8F.
    """

    out = bytearray(len(data) * 2)
    j = 0
    for b in data:
        out[j] = 0x80 | (b >> 4)
        out[j + 1] = 0x80 | (b & 0x0F)
        j += 2
    return bytes(out)


def _try_decode_no_strings(data: bytes) -> bytes | None:
    if not data or (len(data) % 2) != 0:
        return None

    # Quick signature check on the first few bytes.
    sample = data[: min(64, len(data))]
    if any((b & 0xF0) != 0x80 for b in sample):
        return None

    out = bytearray(len(data) // 2)
    j = 0
    for i in range(0, len(data), 2):
        hi = data[i]
        lo = data[i + 1]
        if (hi & 0xF0) != 0x80 or (lo & 0xF0) != 0x80:
            return None
        out[j] = ((hi & 0x0F) << 4) | (lo & 0x0F)
        j += 1
    return bytes(out)


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


def generer_cle_argon2id(mdp: str, salt: bytes, time_cost: int, memory_cost_kib: int, parallelism: int) -> bytes:
    # Import local pour éviter de casser l'app si la dépendance n'est pas encore installée.
    from argon2.low_level import Type, hash_secret_raw

    raw = hash_secret_raw(
        secret=mdp.encode("utf-8"),
        salt=salt,
        time_cost=int(time_cost),
        memory_cost=int(memory_cost_kib),
        parallelism=int(parallelism),
        hash_len=32,
        type=Type.ID,
    )
    return base64.urlsafe_b64encode(raw)


def encoder_v2(token: bytes, salt: bytes, n: int, r: int, p: int) -> bytes:
    return HEADER_V2.pack(MAGIC_V2, salt, n, r, p) + token


def encoder_v3(token: bytes, salt: bytes, n: int, r: int, p: int) -> bytes:
    inner = HEADER_V2.pack(MAGIC_V3, salt, n, r, p) + token
    return _encode_no_strings(inner)


def encoder_v4(token: bytes, salt: bytes, time_cost: int, memory_cost_kib: int, parallelism: int) -> bytes:
    inner = HEADER_V2.pack(MAGIC_V4, salt, time_cost, memory_cost_kib, parallelism) + token
    return _encode_no_strings(inner)


def decoder(data: bytes):
    # V2 (clair) : commence par MAGIC_V2.
    if len(data) >= HEADER_V2.size and data[:4] == MAGIC_V2:
        magic, salt, n, r, p = HEADER_V2.unpack(data[: HEADER_V2.size])
        token = data[HEADER_V2.size :]
        return ("v2", salt, n, r, p, token)

    # V3 : payload encodé (anti-strings), puis header MAGIC_V3.
    decoded = _try_decode_no_strings(data)
    if decoded is not None and len(decoded) >= HEADER_V2.size:
        magic = decoded[:4]
        if magic == MAGIC_V3:
            _magic, salt, n, r, p = HEADER_V2.unpack(decoded[: HEADER_V2.size])
            token = decoded[HEADER_V2.size :]
            return ("v3", salt, n, r, p, token)
        if magic == MAGIC_V4:
            _magic, salt, time_cost, memory_cost_kib, parallelism = HEADER_V2.unpack(decoded[: HEADER_V2.size])
            token = decoded[HEADER_V2.size :]
            return ("v4", salt, time_cost, memory_cost_kib, parallelism, token)
        # Tolérance: si un fichier V2 a été encodé par erreur.
        if magic == MAGIC_V2:
            _magic, salt, n, r, p = HEADER_V2.unpack(decoded[: HEADER_V2.size])
            token = decoded[HEADER_V2.size :]
            return ("v2", salt, n, r, p, token)

    return ("legacy", None, None, None, None, data)


def dechiffrer_bytes(mdp: str, data: bytes) -> bytes:
    version, salt, n, r, p, token = decoder(data)
    if version == "v4":
        cle = generer_cle_argon2id(mdp, salt=salt, time_cost=n, memory_cost_kib=r, parallelism=p)
        return Fernet(cle).decrypt(token)
    if version in {"v2", "v3"}:
        cle = generer_cle_scrypt(mdp, salt=salt, n=n, r=r, p=p)
        return Fernet(cle).decrypt(token)
    cle = generer_cle_legacy_pbkdf2(mdp)
    return Fernet(cle).decrypt(token)


def chiffrer_bytes_v2(mdp: str, contenu: bytes, *, salt: bytes) -> bytes:
    cle = generer_cle_scrypt(mdp, salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    token = Fernet(cle).encrypt(contenu)
    return encoder_v2(token=token, salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)


def chiffrer_bytes_v3(mdp: str, contenu: bytes, *, salt: bytes) -> bytes:
    """Chiffre en v3 (identique v2, mais encodé pour éviter `strings`)."""

    cle = generer_cle_scrypt(mdp, salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    token = Fernet(cle).encrypt(contenu)
    return encoder_v3(token=token, salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)


def chiffrer_bytes_v4(mdp: str, contenu: bytes, *, salt: bytes) -> bytes:
    """Chiffre en v4: Argon2id + Fernet, encodé anti-`strings`."""

    cle = generer_cle_argon2id(
        mdp,
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost_kib=ARGON2_MEMORY_COST_KIB,
        parallelism=ARGON2_PARALLELISM,
    )
    token = Fernet(cle).encrypt(contenu)
    return encoder_v4(
        token=token,
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost_kib=ARGON2_MEMORY_COST_KIB,
        parallelism=ARGON2_PARALLELISM,
    )
