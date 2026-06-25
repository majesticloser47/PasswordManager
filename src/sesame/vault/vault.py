import secrets

import argon2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from sesame.repository import db
from sesame.service.qrng import QRNG


class VaultSession:
    def __init__(self):
        self.vault_key = None
        self.unlocked = False
        self.database = db.DatabaseConnection()
        self.qrng = QRNG()

    def vault_setup(self, master_password: str):
        kdf_salt = secrets.token_bytes(16)

        kdf_memory = 2**16
        kdf_iterations = 3
        kdf_parallelism = 4
        kek = argon2.low_level.hash_secret_raw(
            secret=master_password.encode(),
            salt=kdf_salt,
            time_cost=kdf_iterations,
            memory_cost=kdf_memory,
            parallelism=kdf_parallelism,
            hash_len=32,
            type=argon2.low_level.Type.ID,
        )
        if not self.database.check_vault_exists():
            vault_key_bit_string = self.qrng.get_qrng_sim_rand_bits(32 * 8)  # yayyyy quantum
            vault_key = int(vault_key_bit_string, 2).to_bytes(32, byteorder="big")
            nonce, encrypted_key = self.encrypt_vault_key(vault_key, kek)
            self.database.vault_setup(kdf_salt, kdf_memory, kdf_iterations, kdf_parallelism, nonce, encrypted_key)
            self.unlock(master_password)

    def unlock(self, master_password: str) -> bool:
        vault_info = self.database.fetch_vault_info()
        if not vault_info:
            print("Vault not set up yet. Please set up the vault first.")
            self.vault_setup(master_password)
            vault_info = self.database.fetch_vault_info()
        kdf_salt = vault_info["kdf_salt"]
        kdf_memory = vault_info["kdf_memory"]
        kdf_iterations = vault_info["kdf_iterations"]
        kdf_parallelism = vault_info["kdf_parallelism"]
        key_nonce = vault_info["key_nonce"]
        encrypted_key = vault_info["encrypted_key"]

        kek = argon2.low_level.hash_secret_raw(
            secret=master_password.encode(),
            salt=kdf_salt,
            time_cost=kdf_iterations,
            memory_cost=kdf_memory,
            parallelism=kdf_parallelism,
            hash_len=32,
            type=argon2.low_level.Type.ID,
        )
        try:
            self.vault_key = self.decrypt_vault_key(encrypted_key, kek, key_nonce)
            self.unlocked = True
            return True
        except Exception as e:
            print("Failed to unlock the vault:", e)
            return False

    def encrypt_vault_key(self, vault_key: bytes, kek: bytes) -> tuple[bytes, bytes]:
        nonce = secrets.token_bytes(12)
        aes = AESGCM(kek)
        ciphertext = aes.encrypt(nonce, vault_key, None)
        return (nonce, ciphertext)

    def decrypt_vault_key(self, ciphertext: bytes, kek: bytes, vault_nonce: bytes) -> bytes:
        aes = AESGCM(kek)
        plaintext = aes.decrypt(vault_nonce, ciphertext, None)
        return plaintext
