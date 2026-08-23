import json
import os

import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from sesame.service import password_actions
from sesame.service.password_actions import (
    add_password_entry,
    delete_password_entry,
    get_password_entry_for_service,
    retrieve_pass_list,
)


@pytest.fixture(autouse=True)
def _reset_db_singleton(monkeypatch):
    """Ensure the module-level DB singleton never leaks between tests."""
    monkeypatch.setattr(password_actions, "_db", None)


@pytest.fixture
def mock_db(monkeypatch):
    from unittest.mock import MagicMock

    db = MagicMock()
    monkeypatch.setattr(password_actions, "_db", db)
    return db


def _make_encrypted_entry(entry_id, service, username, notes, password, vault_key):
    data = {
        "service": service,
        "username": username,
        "notes": notes,
        "password": password,
    }
    nonce = os.urandom(12)
    encrypted = AESGCM(vault_key).encrypt(nonce, json.dumps(data).encode(), None)
    return {"id": entry_id, "nonce": nonce, "data": encrypted}


class TestGetDb:
    def test_returns_same_instance_on_repeated_calls(self, mocker, monkeypatch):
        monkeypatch.setattr(password_actions, "_db", None)
        mocker.patch.object(
            password_actions, "DatabaseConnection", return_value="fresh-db"
        )

        first = password_actions._get_db()
        second = password_actions._get_db()

        assert first == "fresh-db"
        assert first is second

    def test_returns_existing_singleton_without_reconstructing(self, mock_db, mocker):
        constructor = mocker.patch.object(password_actions, "DatabaseConnection")

        result = password_actions._get_db()

        assert result is mock_db
        constructor.assert_not_called()


class TestAddPasswordEntry:
    def test_calls_db_with_encrypted_payload(self, mock_db, vault_key):
        mock_db.add_password_entry.return_value = True

        result = add_password_entry("github", "octocat", "note", "s3cr3t", vault_key)

        assert result is True
        mock_db.add_password_entry.assert_called_once()
        call_args = mock_db.add_password_entry.call_args.args
        encrypted_data, nonce = call_args
        assert len(nonce) == 12

        decrypted = AESGCM(vault_key).decrypt(nonce, encrypted_data, None)
        payload = json.loads(decrypted)
        assert payload == {
            "service": "github",
            "username": "octocat",
            "notes": "note",
            "password": "s3cr3t",
        }

    def test_returns_false_when_db_reports_failure(self, mock_db, vault_key):
        mock_db.add_password_entry.return_value = False

        result = add_password_entry("svc", "user", "", "pw", vault_key)

        assert result is False


class TestRetrievePassList:
    def test_returns_empty_list_when_no_entries(self, mock_db, vault_key):
        mock_db.get_all_password_entries.return_value = []

        assert retrieve_pass_list(vault_key) == []

    def test_decrypts_all_entries(self, mock_db, vault_key):
        entry1 = _make_encrypted_entry(1, "github", "u1", "n1", "p1", vault_key)
        entry2 = _make_encrypted_entry(2, "gitlab", "u2", "n2", "p2", vault_key)
        mock_db.get_all_password_entries.return_value = [entry1, entry2]

        result = retrieve_pass_list(vault_key)

        assert result == [
            {
                "id": 1,
                "service": "github",
                "username": "u1",
                "notes": "n1",
                "password": "p1",
            },
            {
                "id": 2,
                "service": "gitlab",
                "username": "u2",
                "notes": "n2",
                "password": "p2",
            },
        ]

    def test_wrong_key_raises_on_decrypt(self, mock_db, vault_key, mocker):
        other_key = os.urandom(32)
        entry = _make_encrypted_entry(1, "svc", "u", "n", "p", other_key)
        mock_db.get_all_password_entries.return_value = [entry]

        with pytest.raises(InvalidTag):
            retrieve_pass_list(vault_key)


class TestGetPasswordEntryForService:
    def test_no_match_prints_warning_and_returns_none(self, mock_db, vault_key, mocker):
        mock_db.get_all_password_entries.return_value = []
        print_mock = mocker.patch.object(password_actions.console, "print")

        result = get_password_entry_for_service("unknown", vault_key)

        assert result is None
        print_mock.assert_called_once()
        assert "No password entries found" in print_mock.call_args.args[0]

    def test_single_match_copies_to_clipboard(self, mock_db, vault_key, mocker):
        entry = _make_encrypted_entry(1, "github", "u", "n", "the-password", vault_key)
        mock_db.get_all_password_entries.return_value = [entry]
        copy_mock = mocker.patch.object(password_actions, "copy_pass_to_clipboard")

        result = get_password_entry_for_service("github", vault_key)

        assert result is None
        copy_mock.assert_called_once_with("the-password")

    def test_multiple_matches_prompts_and_copies_chosen_entry(
        self, mock_db, vault_key, mocker
    ):
        entry1 = _make_encrypted_entry(1, "aws", "u1", "n1", "pw1", vault_key)
        entry2 = _make_encrypted_entry(2, "aws", "u2", "n2", "pw2", vault_key)
        mock_db.get_all_password_entries.return_value = [entry1, entry2]
        mocker.patch.object(password_actions.console, "input", return_value="2")
        copy_mock = mocker.patch.object(password_actions, "copy_pass_to_clipboard")

        get_password_entry_for_service("aws", vault_key)

        copy_mock.assert_called_once_with("pw2")


class TestDeletePasswordEntry:
    def test_confirmed_deletion_calls_db_and_prints_success(
        self, mock_db, vault_key, mocker
    ):
        entry = _make_encrypted_entry(7, "svc", "u", "n", "p", vault_key)
        mock_db.get_all_password_entries.return_value = [entry]
        mocker.patch("builtins.input", return_value="y")
        print_mock = mocker.patch.object(password_actions.console, "print")

        delete_password_entry("svc", vault_key)

        mock_db.delete_password_entry.assert_called_once_with(7)
        assert "has been deleted" in print_mock.call_args.args[0]

    def test_cancelled_deletion_does_not_call_db(self, mock_db, vault_key, mocker):
        entry = _make_encrypted_entry(7, "svc", "u", "n", "p", vault_key)
        mock_db.get_all_password_entries.return_value = [entry]
        mocker.patch("builtins.input", return_value="n")
        print_mock = mocker.patch.object(password_actions.console, "print")

        delete_password_entry("svc", vault_key)

        mock_db.delete_password_entry.assert_not_called()
        assert "cancelled" in print_mock.call_args.args[0]

    def test_invalid_confirmation_input_does_not_call_db(
        self, mock_db, vault_key, mocker
    ):
        entry = _make_encrypted_entry(7, "svc", "u", "n", "p", vault_key)
        mock_db.get_all_password_entries.return_value = [entry]
        mocker.patch("builtins.input", return_value="maybe")
        print_mock = mocker.patch.object(password_actions.console, "print")

        delete_password_entry("svc", vault_key)

        mock_db.delete_password_entry.assert_not_called()
        assert "Invalid input" in print_mock.call_args.args[0]

    def test_service_not_found_prints_warning(self, mock_db, vault_key, mocker):
        mock_db.get_all_password_entries.return_value = []
        print_mock = mocker.patch.object(password_actions.console, "print")

        delete_password_entry("missing-service", vault_key)

        mock_db.delete_password_entry.assert_not_called()
        assert "No password entry found" in print_mock.call_args.args[0]
