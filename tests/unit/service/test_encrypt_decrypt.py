import pytest
from cryptography.exceptions import InvalidTag

from sesame.service.encrypt_decrypt import decrypt, encrypt, generate_key


class TestGenerateKey:
    def test_returns_bytes(self):
        key = generate_key()
        assert isinstance(key, bytes)

    def test_key_is_256_bits(self):
        key = generate_key()
        assert len(key) == 32

    def test_generates_unique_keys(self):
        keys = {generate_key() for _ in range(10)}
        assert len(keys) == 10


class TestEncryptDecryptRoundTrip:
    def test_decrypt_recovers_original_plaintext(self):
        key = generate_key()
        nonce, ciphertext = encrypt("hunter2", key)

        result = decrypt(nonce, ciphertext, key)

        assert result == b"hunter2"

    def test_encrypt_returns_12_byte_nonce(self):
        key = generate_key()
        nonce, _ = encrypt("some text", key)
        assert len(nonce) == 12

    def test_encrypt_uses_fresh_nonce_each_time(self):
        key = generate_key()
        nonce1, _ = encrypt("same text", key)
        nonce2, _ = encrypt("same text", key)
        assert nonce1 != nonce2

    def test_ciphertext_differs_from_plaintext(self):
        key = generate_key()
        _, ciphertext = encrypt("plain-text-value", key)
        assert ciphertext != b"plain-text-value"

    def test_empty_string_round_trips(self):
        key = generate_key()
        nonce, ciphertext = encrypt("", key)
        assert decrypt(nonce, ciphertext, key) == b""

    def test_unicode_content_round_trips(self):
        key = generate_key()
        text = "pässwörd-🔒-日本語"
        nonce, ciphertext = encrypt(text, key)
        assert decrypt(nonce, ciphertext, key) == text.encode()


class TestDecryptFailureModes:
    def test_wrong_key_raises_invalid_tag(self):
        key = generate_key()
        wrong_key = generate_key()
        nonce, ciphertext = encrypt("secret", key)

        with pytest.raises(InvalidTag):
            decrypt(nonce, ciphertext, wrong_key)

    def test_wrong_nonce_raises_invalid_tag(self):
        key = generate_key()
        nonce, ciphertext = encrypt("secret", key)
        _, other_nonce = encrypt("secret", key)

        with pytest.raises(InvalidTag):
            decrypt(other_nonce, ciphertext, key)

    def test_tampered_ciphertext_raises_invalid_tag(self):
        key = generate_key()
        nonce, ciphertext = encrypt("secret", key)
        tampered = bytes([ciphertext[0] ^ 0xFF]) + ciphertext[1:]

        with pytest.raises(InvalidTag):
            decrypt(nonce, tampered, key)
