from unittest.mock import MagicMock

import pytest

from sesame import sesame as sesame_module
from sesame.service.enum.entropy_sources_enum import EntropySourceEnum
from sesame.sesame import SesameShell


@pytest.fixture
def vault():
    v = MagicMock()
    v.unlocked = False
    v.vault_key = b"key"
    return v


@pytest.fixture
def shell(vault):
    shell = SesameShell(vault, EntropySourceEnum.CSPRNG)
    shell.console = MagicMock()
    return shell


class TestInit:
    def test_starts_with_locked_prompt(self, vault):
        shell = SesameShell(vault, EntropySourceEnum.CSPRNG)
        assert "closed sesame" in shell.prompt or shell.prompt.endswith(" > ")

    def test_stores_vault_and_entropy_mode(self, shell, vault):
        assert shell.vault is vault
        assert shell.entropy_mode == EntropySourceEnum.CSPRNG


class TestDoUnlock:
    def test_successful_unlock_updates_prompt(self, shell, vault, mocker):
        mocker.patch.object(sesame_module.getpass, "getpass", return_value="pw")
        vault.unlock.return_value = True
        vault.unlocked = True

        shell.do_unlock("")

        vault.unlock.assert_called_once_with("pw")
        shell.console.print.assert_any_call(
            "[green]✔  Vault unlocked successfully.[/green]"
        )

    def test_failed_unlock_prints_error(self, shell, vault, mocker):
        mocker.patch.object(sesame_module.getpass, "getpass", return_value="pw")
        vault.unlock.side_effect = ValueError("bad kdf params")

        shell.do_unlock("")

        printed = shell.console.print.call_args.args[0]
        assert "Failed to unlock vault" in printed


class TestDoAdd:
    def test_locked_vault_prints_locked_message(self, shell, vault, mocker):
        vault.unlocked = False
        add_mock = mocker.patch.object(sesame_module, "add_password_entry")

        shell.do_add("")

        add_mock.assert_not_called()
        shell.console.print.assert_called_once_with(shell.vault_locked_message)

    def test_generated_password_is_added_and_copied(self, shell, vault, mocker):
        vault.unlocked = True
        shell.console.input.side_effect = [
            "github",
            "octocat",
            "note",
            "y",
            "12",
        ]
        mocker.patch.object(
            shell.password_generator, "generate_password", return_value="gen-pw"
        )
        add_mock = mocker.patch.object(sesame_module, "add_password_entry")
        copy_mock = mocker.patch.object(sesame_module, "copy_pass_to_clipboard")

        shell.do_add("")

        add_mock.assert_called_once_with(
            "github", "octocat", "note", "gen-pw", vault.vault_key
        )
        copy_mock.assert_called_once_with("gen-pw")

    def test_manual_password_is_added_without_copy(self, shell, vault, mocker):
        vault.unlocked = True
        shell.console.input.side_effect = ["svc", "user", "", "n"]
        mocker.patch.object(sesame_module.getpass, "getpass", return_value="manual-pw")
        add_mock = mocker.patch.object(sesame_module, "add_password_entry")
        copy_mock = mocker.patch.object(sesame_module, "copy_pass_to_clipboard")

        shell.do_add("")

        add_mock.assert_called_once_with(
            "svc", "user", "", "manual-pw", vault.vault_key
        )
        copy_mock.assert_not_called()


class TestDoList:
    def test_locked_vault_prints_locked_message(self, shell, vault, mocker):
        vault.unlocked = False
        retrieve_mock = mocker.patch.object(sesame_module, "retrieve_pass_list")

        shell.do_list("")

        retrieve_mock.assert_not_called()
        shell.console.print.assert_called_once_with(shell.vault_locked_message)

    def test_unlocked_with_entries_prints_table(self, shell, vault, mocker):
        vault.unlocked = True
        mocker.patch.object(
            sesame_module,
            "retrieve_pass_list",
            return_value=[
                {"service": "svc", "username": "u", "notes": "n", "password": "p"}
            ],
        )

        shell.do_list("")

        shell.console.print.assert_called_once()

    def test_unlocked_with_no_entries_prints_warning(self, shell, vault, mocker):
        vault.unlocked = True
        mocker.patch.object(sesame_module, "retrieve_pass_list", return_value=[])

        shell.do_list("")

        shell.console.print.assert_called_once_with(
            "[yellow]⚠  No password entries found.[/yellow]"
        )


class TestDoFetch:
    def test_empty_service_prints_warning(self, shell, vault, mocker):
        vault.unlocked = True
        fetch_mock = mocker.patch.object(
            sesame_module, "get_password_entry_for_service"
        )

        shell.do_fetch("   ")

        fetch_mock.assert_not_called()
        shell.console.print.assert_called_once_with(
            "[yellow]⚠  Please provide a service name.[/yellow]"
        )

    def test_valid_service_calls_lookup(self, shell, vault, mocker):
        vault.unlocked = True
        fetch_mock = mocker.patch.object(
            sesame_module, "get_password_entry_for_service"
        )

        shell.do_fetch("github")

        fetch_mock.assert_called_once_with("github", vault.vault_key)

    def test_locked_vault_does_not_call_lookup(self, shell, vault, mocker):
        # NOTE: do_fetch has no `else` branch for the locked case (unlike the
        # other commands), so no message is printed either - this test
        # documents that existing behaviour.
        vault.unlocked = False
        fetch_mock = mocker.patch.object(
            sesame_module, "get_password_entry_for_service"
        )

        shell.do_fetch("github")

        fetch_mock.assert_not_called()
        shell.console.print.assert_not_called()


class TestDoDelete:
    def test_locked_vault_prints_locked_message(self, shell, vault, mocker):
        vault.unlocked = False
        delete_mock = mocker.patch.object(sesame_module, "delete_password_entry")

        shell.do_delete("github")

        delete_mock.assert_not_called()
        shell.console.print.assert_called_once_with(shell.vault_locked_message)

    def test_empty_service_prints_warning(self, shell, vault, mocker):
        vault.unlocked = True
        delete_mock = mocker.patch.object(sesame_module, "delete_password_entry")

        shell.do_delete("   ")

        delete_mock.assert_not_called()
        shell.console.print.assert_called_once_with(
            "[yellow]⚠  Please provide a service name.[/yellow]"
        )

    def test_valid_service_calls_delete(self, shell, vault, mocker):
        vault.unlocked = True
        delete_mock = mocker.patch.object(sesame_module, "delete_password_entry")

        shell.do_delete("github")

        delete_mock.assert_called_once_with("github", vault.vault_key)


class TestDoLock:
    def test_unlocked_vault_gets_locked(self, shell, vault):
        vault.unlocked = True

        shell.do_lock("")

        vault.lock.assert_called_once()

    def test_already_locked_vault_prints_message(self, shell, vault):
        vault.unlocked = False

        shell.do_lock("")

        vault.lock.assert_not_called()
        shell.console.print.assert_called_once_with(
            "[yellow]⚠  Vault is already locked.[/yellow]"
        )


class TestDoExit:
    def test_prints_farewell_and_returns_true(self, shell):
        result = shell.do_exit("")
        assert result is True
        shell.console.print.assert_called_once()


class TestStart:
    def test_prints_panel_and_starts_cmdloop(self, shell, mocker):
        cmdloop_mock = mocker.patch.object(shell, "cmdloop")

        shell.start()

        cmdloop_mock.assert_called_once()
        shell.console.print.assert_called_once()

    def test_shows_quantum_mode_label(self, vault, mocker):
        shell = SesameShell(vault, EntropySourceEnum.QRNG)
        shell.console = MagicMock()
        mocker.patch.object(shell, "cmdloop")

        shell.start()

        panel_arg = shell.console.print.call_args.args[0]
        assert "Quantum Mode" in panel_arg.renderable
