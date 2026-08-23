import pytest
from cryptography.exceptions import InvalidTag

from sesame.vault.vault import VaultSession
from tests.helpers import FakeEntropySource


@pytest.fixture
def vault_session(database_connection, mock_console):
    entropy = FakeEntropySource([123456789])
    return VaultSession(database_connection, entropy, mock_console)


class TestVaultSetup:
    def test_creates_vault_row_when_none_exists(
        self, vault_session, database_connection
    ):
        assert database_connection.check_vault_exists() is False

        vault_session.vault_setup("master-password")

        assert database_connection.check_vault_exists() is True

    def test_unlocks_after_setup(self, vault_session):
        vault_session.vault_setup("master-password")

        assert vault_session.unlocked is True
        assert vault_session.vault_key is not None
        assert len(vault_session.vault_key) == 32

    def test_does_nothing_when_vault_already_exists(
        self, database_connection, mock_console
    ):
        entropy = FakeEntropySource([1])
        session = VaultSession(database_connection, entropy, mock_console)
        session.vault_setup("master-password")
        original_info = database_connection.fetch_vault_info()

        # A second call with a vault already present must be a no-op.
        session.vault_setup("master-password")

        assert database_connection.fetch_vault_info() == original_info


class TestUnlock:
    def test_sets_up_vault_automatically_on_first_unlock(
        self, vault_session, database_connection
    ):
        result = vault_session.unlock("master-password")

        assert result is True
        assert database_connection.check_vault_exists() is True
        assert vault_session.unlocked is True

    def test_correct_password_unlocks_existing_vault(
        self, database_connection, mock_console
    ):
        setup_session = VaultSession(
            database_connection, FakeEntropySource([42]), mock_console
        )
        setup_session.unlock("correct-password")

        fresh_session = VaultSession(
            database_connection, FakeEntropySource([42]), mock_console
        )
        result = fresh_session.unlock("correct-password")

        assert result is True
        assert fresh_session.vault_key == setup_session.vault_key

    def test_wrong_password_fails_to_unlock(self, database_connection, mock_console):
        setup_session = VaultSession(
            database_connection, FakeEntropySource([42]), mock_console
        )
        setup_session.unlock("correct-password")

        fresh_session = VaultSession(
            database_connection, FakeEntropySource([42]), mock_console
        )
        result = fresh_session.unlock("wrong-password")

        assert result is False
        assert fresh_session.unlocked is False
        assert fresh_session.vault_key is None

    def test_wrong_password_prints_error_message(
        self, database_connection, mock_console
    ):
        setup_session = VaultSession(
            database_connection, FakeEntropySource([42]), mock_console
        )
        setup_session.unlock("correct-password")

        fresh_session = VaultSession(
            database_connection, FakeEntropySource([42]), mock_console
        )
        fresh_session.unlock("wrong-password")

        printed = " ".join(str(c.args[0]) for c in mock_console.print.call_args_list)
        assert "Failed to unlock" in printed


class TestLock:
    def test_resets_unlocked_state(self, vault_session):
        vault_session.unlock("master-password")

        vault_session.lock()

        assert vault_session.unlocked is False
        assert vault_session.vault_key is None

    def test_prints_locked_message(self, vault_session, mock_console):
        vault_session.lock()
        mock_console.print.assert_called_with(
            "[yellow]⚠  Vault is now locked.[/yellow]"
        )


class TestEncryptDecryptVaultKey:
    def test_round_trips_vault_key(self, vault_session):
        vault_key = b"0" * 32
        kek = b"1" * 32

        nonce, ciphertext = vault_session.encrypt_vault_key(vault_key, kek)
        result = vault_session.decrypt_vault_key(ciphertext, kek, nonce)

        assert result == vault_key

    def test_nonce_is_12_bytes(self, vault_session):
        nonce, _ = vault_session.encrypt_vault_key(b"0" * 32, b"1" * 32)
        assert len(nonce) == 12

    def test_wrong_kek_fails_to_decrypt(self, vault_session):
        nonce, ciphertext = vault_session.encrypt_vault_key(b"0" * 32, b"1" * 32)

        with pytest.raises(InvalidTag):
            vault_session.decrypt_vault_key(ciphertext, b"2" * 32, nonce)
