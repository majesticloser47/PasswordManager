import time
from rich.console import Console
import pyperclip

console = Console()


def copy_pass_to_clipboard(text):
    try:
        previous = pyperclip.paste()
        pyperclip.copy(text)
        console.print(
            "[green]✔  Password copied to clipboard. It will be cleared in 20 seconds.[/green]"
        )
        time.sleep(20)
        if pyperclip.paste() == text:
            clear_clipboard(previous)

    except KeyboardInterrupt:
        print("Program interrupted, clearing clipboard")
        clear_clipboard(previous)
        exit(0)


def clear_clipboard(previous_text=""):
    pyperclip.copy(previous_text)
    console.print("[yellow]⚠  Clipboard cleared.[/yellow]")
