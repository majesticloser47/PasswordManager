import sqlite3

from sesame.repository.db import DatabaseConnection


class TestInitDb:
    def test_creates_vault_table(self, database_connection):
        cursor = database_connection.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vault'"
        )
        assert cursor.fetchone() is not None

    def test_creates_entries_table(self, database_connection):
        cursor = database_connection.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
        )
        assert cursor.fetchone() is not None

    def test_creates_expected_triggers(self, database_connection):
        cursor = database_connection.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
        trigger_names = {row["name"] for row in cursor.fetchall()}
        assert {"trg_vault_updated_at", "trg_entries_updated_at"} <= trigger_names

    def test_row_factory_allows_dict_like_access(self, database_connection):
        database_connection.conn.execute(
            "INSERT INTO entries (nonce, data) VALUES (?, ?)", (b"n", b"d")
        )
        database_connection.conn.commit()
        row = database_connection.conn.execute("SELECT * FROM entries").fetchone()
        assert row["nonce"] == b"n"

    def test_is_idempotent_when_called_again(self, database_connection):
        # Calling init_db a second time on an already-initialized DB must not
        # raise, since all statements use "IF NOT EXISTS".
        database_connection.init_db()

    def test_file_backed_db_persists_across_connections(self, fake_db_config, db_path):
        db1 = DatabaseConnection(config=fake_db_config)
        db1.vault_setup(b"salt", 65536, 3, 4, b"nonce", b"enc-key")
        db1.conn.close()

        db2 = DatabaseConnection(config=fake_db_config)
        info = db2.fetch_vault_info()
        assert info["kdf_salt"] == b"salt"
        db2.conn.close()


class TestCheckVaultExists:
    def test_returns_false_when_no_vault_row(self, database_connection):
        assert database_connection.check_vault_exists() is False

    def test_returns_true_after_vault_setup(self, database_connection):
        database_connection.vault_setup(b"salt", 65536, 3, 4, b"nonce", b"enc-key")
        assert database_connection.check_vault_exists() is True


class TestVaultSetup:
    def test_returns_true_on_success(self, database_connection):
        assert (
            database_connection.vault_setup(b"salt", 65536, 3, 4, b"nonce", b"enc-key")
            is True
        )

    def test_stores_all_fields(self, database_connection):
        database_connection.vault_setup(
            b"my-salt", 131072, 5, 2, b"my-nonce", b"my-enc-key"
        )
        info = database_connection.fetch_vault_info()
        assert info == {
            "kdf_salt": b"my-salt",
            "kdf_memory": 131072,
            "kdf_iterations": 5,
            "kdf_parallelism": 2,
            "key_nonce": b"my-nonce",
            "encrypted_key": b"my-enc-key",
        }

    def test_second_call_replaces_existing_row(self, database_connection):
        database_connection.vault_setup(b"first", 1, 1, 1, b"n1", b"e1")
        database_connection.vault_setup(b"second", 2, 2, 2, b"n2", b"e2")

        info = database_connection.fetch_vault_info()
        assert info["kdf_salt"] == b"second"
        cursor = database_connection.conn.execute("SELECT COUNT(*) as c FROM vault")
        assert cursor.fetchone()["c"] == 1


class TestFetchVaultInfo:
    def test_returns_none_when_not_set_up(self, database_connection):
        assert database_connection.fetch_vault_info() is None


class TestPasswordEntries:
    def test_add_password_entry_returns_true(self, database_connection):
        assert database_connection.add_password_entry(b"data", b"nonce") is True

    def test_get_all_password_entries_empty_initially(self, database_connection):
        assert database_connection.get_all_password_entries() == []

    def test_get_all_password_entries_returns_added_entries(self, database_connection):
        database_connection.add_password_entry(b"data1", b"nonce1")
        database_connection.add_password_entry(b"data2", b"nonce2")

        entries = database_connection.get_all_password_entries()

        assert len(entries) == 2
        assert {e["data"] for e in entries} == {b"data1", b"data2"}
        assert {e["nonce"] for e in entries} == {b"nonce1", b"nonce2"}
        assert all("id" in e for e in entries)

    def test_delete_password_entry_removes_row(self, database_connection):
        database_connection.add_password_entry(b"data", b"nonce")
        entry_id = database_connection.get_all_password_entries()[0]["id"]

        database_connection.delete_password_entry(entry_id)

        assert database_connection.get_all_password_entries() == []

    def test_delete_password_entry_with_unknown_id_is_noop(self, database_connection):
        database_connection.add_password_entry(b"data", b"nonce")

        database_connection.delete_password_entry(99999)

        assert len(database_connection.get_all_password_entries()) == 1


class TestDatabaseConnectionConstruction:
    def test_defaults_to_config_when_none_provided(self, mocker, fake_db_config):
        mocker.patch("sesame.repository.db.Config", return_value=fake_db_config)
        connection = DatabaseConnection(config=None)
        assert connection.db_path == fake_db_config.vault_db_path
        connection.conn.close()

    def test_uses_sqlite_connection(self, database_connection):
        assert isinstance(database_connection.conn, sqlite3.Connection)
