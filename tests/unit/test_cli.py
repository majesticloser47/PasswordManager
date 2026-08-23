import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from rich.console import Console
from typer.testing import CliRunner

from sesame.cli import (
    _migrate_db_file,
    _prepare_db_path,
    _run_first_time_setup,
    app,
    main,
)
from sesame.service.enum.entropy_sources_enum import EntropySourceEnum

runner = CliRunner()


class TestPrepareDbPath:
    def test_expands_user_and_makes_absolute(self, tmp_path, mocker):
        mocker.patch("os.path.expanduser", side_effect=lambda p: p)
        result = _prepare_db_path(str(tmp_path / "sub" / "vault.db"))
        assert os.path.isabs(result)

    def test_strips_surrounding_whitespace_and_quotes(self, tmp_path):
        raw = f'  "{tmp_path / "vault.db"}"  '
        result = _prepare_db_path(raw)
        assert result == os.path.abspath(str(tmp_path / "vault.db"))

    def test_creates_parent_directory(self, tmp_path):
        target = tmp_path / "nested" / "dir" / "vault.db"
        _prepare_db_path(str(target))
        assert os.path.isdir(target.parent)


class TestMigrateDbFile:
    def test_noop_when_paths_are_identical(self, tmp_path, mocker):
        move_mock = mocker.patch("sesame.cli.shutil.move")
        path = str(tmp_path / "vault.db")

        _migrate_db_file(path, path, Console())

        move_mock.assert_not_called()

    def test_noop_when_old_path_missing(self, tmp_path, mocker):
        move_mock = mocker.patch("sesame.cli.shutil.move")

        _migrate_db_file(
            str(tmp_path / "missing.db"), str(tmp_path / "new.db"), Console()
        )

        move_mock.assert_not_called()

    def test_warns_and_skips_when_new_path_already_exists(self, tmp_path, mocker):
        old_path = tmp_path / "old.db"
        new_path = tmp_path / "new.db"
        old_path.write_text("old")
        new_path.write_text("new")
        move_mock = mocker.patch("sesame.cli.shutil.move")
        console = MagicMock()

        _migrate_db_file(str(old_path), str(new_path), console)

        move_mock.assert_not_called()
        console.print.assert_called_once()
        assert "already exists" in console.print.call_args.args[0]

    def test_moves_file_when_safe(self, tmp_path):
        old_path = tmp_path / "old.db"
        new_path = tmp_path / "new.db"
        old_path.write_text("data")
        console = MagicMock()

        _migrate_db_file(str(old_path), str(new_path), console)

        assert not old_path.exists()
        assert new_path.read_text() == "data"
        assert "Moved vault database" in console.print.call_args.args[0]

    def test_raises_and_prints_error_on_os_error(self, tmp_path, mocker):
        old_path = tmp_path / "old.db"
        old_path.write_text("data")
        new_path = tmp_path / "new.db"
        mocker.patch("sesame.cli.shutil.move", side_effect=OSError("disk full"))
        console = MagicMock()

        with pytest.raises(OSError):
            _migrate_db_file(str(old_path), str(new_path), console)

        assert "Failed to move vault database" in console.print.call_args.args[0]


class TestRunFirstTimeSetup:
    def _fake_config(self, default_path="/default/path.db"):
        config = MagicMock()
        config.get_configurable_value.return_value = default_path
        return config

    def test_declining_change_keeps_default_and_marks_complete(self, mocker):
        config = self._fake_config()
        console = MagicMock()
        mocker.patch.object(console, "input", return_value="n")

        _run_first_time_setup(config, console)

        config.set_configurable_value.assert_not_called()
        config.mark_setup_complete.assert_called_once()

    def test_accepting_change_with_valid_path_updates_config(self, mocker, tmp_path):
        config = self._fake_config()
        console = MagicMock()
        new_path = str(tmp_path / "custom" / "vault.db")
        console.input.side_effect = ["y", new_path]

        _run_first_time_setup(config, console)

        config.set_configurable_value.assert_called_once()
        args = config.set_configurable_value.call_args.args
        assert args[0] == "db_path"
        assert os.path.isabs(args[1])
        config.mark_setup_complete.assert_called_once()

    def test_accepting_change_with_blank_path_does_not_update(self, mocker):
        config = self._fake_config()
        console = MagicMock()
        console.input.side_effect = ["yes", "   "]

        _run_first_time_setup(config, console)

        config.set_configurable_value.assert_not_called()
        config.mark_setup_complete.assert_called_once()


class TestMainCallback:
    def _patch_collaborators(self, mocker, is_first_run=False):
        config = MagicMock(is_first_run=is_first_run)
        mocker.patch("sesame.cli.Config", return_value=config)
        db_instance = MagicMock()
        mocker.patch("sesame.cli.db.DatabaseConnection", return_value=db_instance)
        entropy_source = MagicMock()
        factory = mocker.patch(
            "sesame.cli.create_entropy_source_factory", return_value=entropy_source
        )
        vault_instance = MagicMock()
        vault_cls = mocker.patch("sesame.cli.VaultSession", return_value=vault_instance)
        shell_instance = MagicMock()
        shell_cls = mocker.patch("sesame.cli.SesameShell", return_value=shell_instance)
        return {
            "config": config,
            "db_instance": db_instance,
            "factory": factory,
            "vault_cls": vault_cls,
            "vault_instance": vault_instance,
            "shell_cls": shell_cls,
            "shell_instance": shell_instance,
        }

    def test_returns_immediately_when_subcommand_invoked(self, mocker):
        config_cls = mocker.patch("sesame.cli.Config")
        ctx = SimpleNamespace(invoked_subcommand="config")

        main(ctx, mode=EntropySourceEnum.CSPRNG)

        config_cls.assert_not_called()

    def test_starts_shell_when_no_subcommand(self, mocker):
        mocks = self._patch_collaborators(mocker)
        ctx = SimpleNamespace(invoked_subcommand=None)

        main(ctx, mode=EntropySourceEnum.CSPRNG)

        mocks["vault_cls"].assert_called_once_with(
            mocks["db_instance"], mocks["factory"].return_value, mocker.ANY
        )
        mocks["shell_cls"].assert_called_once_with(
            mocks["vault_instance"], EntropySourceEnum.CSPRNG
        )
        mocks["shell_instance"].start.assert_called_once()

    def test_runs_first_time_setup_when_first_run(self, mocker):
        setup_mock = mocker.patch("sesame.cli._run_first_time_setup")
        ctx = SimpleNamespace(invoked_subcommand=None)

        main(ctx, mode=EntropySourceEnum.CSPRNG)

        setup_mock.assert_called_once()

    def test_skips_first_time_setup_when_already_done(self, mocker):
        setup_mock = mocker.patch("sesame.cli._run_first_time_setup")
        ctx = SimpleNamespace(invoked_subcommand=None)

        main(ctx, mode=EntropySourceEnum.CSPRNG)

        setup_mock.assert_not_called()

    def test_keyboard_interrupt_clears_clipboard_and_exits(self, mocker):
        mocks = self._patch_collaborators(mocker)
        mocks["shell_instance"].start.side_effect = KeyboardInterrupt
        clear_mock = mocker.patch("sesame.cli.clear_clipboard")
        ctx = SimpleNamespace(invoked_subcommand=None)

        with pytest.raises(SystemExit) as exc_info:
            main(ctx, mode=EntropySourceEnum.CSPRNG)

        assert exc_info.value.code == 0
        clear_mock.assert_called_once()


class TestConfigCommand:
    def _patch_config(self, mocker, current_value="/default/vault.db"):
        from sesame.config import Config as RealConfig

        config_cls = mocker.patch("sesame.cli.Config")
        config_cls.configurable_keys = RealConfig.configurable_keys
        instance = MagicMock()
        instance.get_configurable_value.return_value = current_value
        config_cls.return_value = instance
        return instance

    def test_quit_makes_no_changes(self, mocker):
        instance = self._patch_config(mocker)

        result = runner.invoke(app, ["config"], input="q\n")

        assert result.exit_code == 0
        instance.set_configurable_value.assert_not_called()

    def test_empty_input_cancels(self, mocker):
        instance = self._patch_config(mocker)

        result = runner.invoke(app, ["config"], input="\n")

        assert result.exit_code == 0
        instance.set_configurable_value.assert_not_called()

    def test_invalid_index_reports_error(self, mocker):
        instance = self._patch_config(mocker)

        result = runner.invoke(app, ["config"], input="99\n")

        assert result.exit_code == 0
        assert "Invalid choice" in result.output
        instance.set_configurable_value.assert_not_called()

    def test_non_numeric_index_reports_error(self, mocker):
        instance = self._patch_config(mocker)

        result = runner.invoke(app, ["config"], input="abc\n")

        assert result.exit_code == 0
        assert "Invalid choice" in result.output
        instance.set_configurable_value.assert_not_called()

    def test_blank_value_makes_no_changes(self, mocker):
        instance = self._patch_config(mocker)

        result = runner.invoke(app, ["config"], input="1\n   \n")

        assert result.exit_code == 0
        assert "No value entered" in result.output
        instance.set_configurable_value.assert_not_called()

    def test_valid_new_db_path_updates_config(self, mocker, tmp_path):
        instance = self._patch_config(
            mocker, current_value=str(tmp_path / "missing-old.db")
        )
        new_path = tmp_path / "new-location" / "vault.db"

        result = runner.invoke(app, ["config"], input=f"1\n{new_path}\n")

        assert result.exit_code == 0
        instance.set_configurable_value.assert_called_once()
        call_args = instance.set_configurable_value.call_args.args
        assert call_args[0] == "db_path"
        assert os.path.abspath(str(new_path)) == call_args[1]
        instance.mark_setup_complete.assert_called_once()
