import os

import pytest
from cryptography.fernet import InvalidToken

from mdp_app.crypto import chiffrer_bytes_v2, chiffrer_bytes_v3, chiffrer_bytes_v4, dechiffrer_bytes, decoder


def test_v4_roundtrip_and_decoder_version():
    mdp = "correct horse battery staple"
    plaintext = b"hello\nsecret\n"

    blob = chiffrer_bytes_v4(mdp, plaintext, salt=os.urandom(16))
    version, *_rest = decoder(blob)
    assert version == "v4"

    out = dechiffrer_bytes(mdp, blob)
    assert out == plaintext


def test_v4_wrong_password_raises():
    mdp = "pw1"
    plaintext = b"data"
    blob = chiffrer_bytes_v4(mdp, plaintext, salt=os.urandom(16))

    with pytest.raises(InvalidToken):
        dechiffrer_bytes("wrong", blob)


def test_v3_and_v2_decoding_works():
    mdp = "pw"
    plaintext = b"abc"

    blob_v2 = chiffrer_bytes_v2(mdp, plaintext, salt=os.urandom(16))
    assert decoder(blob_v2)[0] == "v2"
    assert dechiffrer_bytes(mdp, blob_v2) == plaintext

    blob_v3 = chiffrer_bytes_v3(mdp, plaintext, salt=os.urandom(16))
    assert decoder(blob_v3)[0] == "v3"
    assert dechiffrer_bytes(mdp, blob_v3) == plaintext


def test_v4_is_encoded_no_strings_style():
    mdp = "pw"
    plaintext = b"something"
    blob = chiffrer_bytes_v4(mdp, plaintext, salt=os.urandom(16))

    # v4 payload is encoded so bytes should be in 0x80..0x8F (high nibble 0x8)
    sample = blob[: min(256, len(blob))]
    assert sample, "empty blob"
    assert all((b & 0xF0) == 0x80 for b in sample)
