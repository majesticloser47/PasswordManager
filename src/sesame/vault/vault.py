import secrets

import argon2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class VaultSession:
    def __init__(self, database, random_number_source, console):
        self.vault_key = None
        self.unlocked = False
        self.database = database
        self.random_number_source = random_number_source
        self.console = console

    def vault_setup(self, master_password: str):
        if not self.database.check_vault_exists():
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
            vault_key = self.random_number_source.randbelow(2 ** (32 * 8)).to_bytes(
                32, byteorder="big"
            )  # yayyyy quantum
            nonce, encrypted_key = self.encrypt_vault_key(vault_key, kek)
            self.database.vault_setup(
                kdf_salt,
                kdf_memory,
                kdf_iterations,
                kdf_parallelism,
                nonce,
                encrypted_key,
            )
            self.unlock(master_password)

    def unlock(self, master_password: str) -> bool:
        vault_info = self.database.fetch_vault_info()
        if not vault_info:
            self.console.print(
                "[yellow]⚠  Vault not set up yet - setting up now...[/yellow]"
            )
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
            self.console.print(f"[red]✘  Failed to unlock the vault:[/red] {e}")
            return False

    def lock(self):
        self.unlocked = False
        self.vault_key = None
        self.console.print("[yellow]⚠  Vault is now locked.[/yellow]")

    def encrypt_vault_key(self, vault_key: bytes, kek: bytes) -> tuple[bytes, bytes]:
        nonce = secrets.token_bytes(12)
        aes = AESGCM(kek)
        ciphertext = aes.encrypt(nonce, vault_key, None)
        return (nonce, ciphertext)

    def decrypt_vault_key(
        self, ciphertext: bytes, kek: bytes, vault_nonce: bytes
    ) -> bytes:
        aes = AESGCM(kek)
        plaintext = aes.decrypt(vault_nonce, ciphertext, None)
        return plaintext
