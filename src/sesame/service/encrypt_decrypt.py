import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)


def encrypt(plaintext: bytes, key: bytes) -> tuple[bytes, bytes]:
    nonce = secrets.token_bytes(12)
    aes = AESGCM(key)

    ciphertext = aes.encrypt(nonce, plaintext.encode(), None)
    return (nonce, ciphertext)


def decrypt(nonce: bytes, ciphertext: bytes, key: bytes) -> bytes:
    aes = AESGCM(key)
    plaintext = aes.decrypt(nonce, ciphertext, None)
    return plaintext
