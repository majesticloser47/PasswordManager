from sesame.service.enum.entropy_sources_enum import EntropySourceEnum
from sesame.util.functions import clear_clipboard
from sesame.sesame import SesameShell
from sesame.vault.vault import VaultSession
import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    mode: EntropySourceEnum = typer.Option(
        EntropySourceEnum.CSPRNG,
        "--mode",
        help="Source of entropy for randomness (CSPRNG or QRNG)",
    ),
):
    try:
        if ctx.invoked_subcommand is not None:
            return
        vault = VaultSession()  # Initialize the vault session
        sesame_shell = SesameShell(vault, mode)
        sesame_shell.start()
    except KeyboardInterrupt:
        print("Sesame interrupted, clearing clipboard and exiting...bye byeee!")
        clear_clipboard()
        exit(0)
