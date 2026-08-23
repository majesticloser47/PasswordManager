import pytest

from sesame.util import functions as functions_module
from sesame.util.functions import clear_clipboard, copy_pass_to_clipboard


@pytest.fixture(autouse=True)
def _no_real_sleep(mocker):
    """Never actually sleep for 20 seconds during tests."""
    return mocker.patch.object(functions_module.time, "sleep")


class TestCopyPassToClipboard:
    def test_copies_text_to_clipboard(self, mocker):
        mocker.patch.object(functions_module.pyperclip, "paste", return_value="text")
        copy_mock = mocker.patch.object(functions_module.pyperclip, "copy")

        copy_pass_to_clipboard("text")

        copy_mock.assert_any_call("text")

    def test_sleeps_for_twenty_seconds(self, mocker):
        mocker.patch.object(functions_module.pyperclip, "paste", return_value="text")
        mocker.patch.object(functions_module.pyperclip, "copy")
        sleep_mock = mocker.patch.object(functions_module.time, "sleep")

        copy_pass_to_clipboard("text")

        sleep_mock.assert_called_once_with(20)

    def test_restores_previous_clipboard_if_unchanged_after_wait(self, mocker):
        mocker.patch.object(
            functions_module.pyperclip, "paste", side_effect=["previous-value", "text"]
        )
        copy_mock = mocker.patch.object(functions_module.pyperclip, "copy")

        copy_pass_to_clipboard("text")

        assert copy_mock.call_args_list[-1].args[0] == "previous-value"

    def test_does_not_restore_if_clipboard_changed_during_wait(self, mocker):
        mocker.patch.object(
            functions_module.pyperclip,
            "paste",
            side_effect=["previous-value", "something-else"],
        )
        copy_mock = mocker.patch.object(functions_module.pyperclip, "copy")

        copy_pass_to_clipboard("text")

        # Only the initial copy(text) call should have happened.
        copy_mock.assert_called_once_with("text")

    def test_keyboard_interrupt_during_wait_clears_clipboard_and_exits(self, mocker):
        mocker.patch.object(
            functions_module.pyperclip, "paste", return_value="previous"
        )
        mocker.patch.object(functions_module.pyperclip, "copy")
        mocker.patch.object(
            functions_module.time, "sleep", side_effect=KeyboardInterrupt
        )
        clear_mock = mocker.patch.object(functions_module, "clear_clipboard")

        with pytest.raises(SystemExit) as exc_info:
            copy_pass_to_clipboard("text")

        assert exc_info.value.code == 0
        clear_mock.assert_called_once_with("previous")


class TestClearClipboard:
    def test_copies_previous_text_back(self, mocker):
        copy_mock = mocker.patch.object(functions_module.pyperclip, "copy")

        clear_clipboard("previous-secret")

        copy_mock.assert_called_once_with("previous-secret")

    def test_defaults_to_empty_string(self, mocker):
        copy_mock = mocker.patch.object(functions_module.pyperclip, "copy")

        clear_clipboard()

        copy_mock.assert_called_once_with("")
