import os

from sesame.service.entropy_sources.entropy_factory import create_entropy_source_factory
from sesame.service.enum.entropy_sources_enum import EntropySourceEnum
from sesame.util.functions import clear_clipboard
from sesame.sesame import SesameShell
from sesame.vault.vault import VaultSession
import typer
from sesame.repository import db
from rich.console import Console
from sesame.config import Config

app = typer.Typer()


def _prepare_db_path(raw_path: str):
    path = os.path.abspath(os.path.expanduser(raw_path.strip().strip('"')))
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path


def _run_first_time_setup(config: Config, console: Console):
    default_path = config.get_configurable_value("db_path")
    console.print(
        "[bold cyan]Welcome to Sesame![/bold cyan] Let's finish setting things up.\n"
    )
    console.print(
        f"The vault database will be stored at:\n  [cyan]{default_path}[/cyan]\n"
    )
    change = (
        console.input(
            "Would you like to store it at a different location instead? (y/N): "
        )
        .strip()
        .lower()
    )
    if change in ("y", "yes"):
        raw_path = console.input("Enter the new path for the vault database: ")
        if raw_path.strip():
            new_path = _prepare_db_path(raw_path)
            config.set_configurable_value("db_path", new_path)
            console.print(
                f"[green]✔  Vault database location set to:[/green] {new_path}\n"
            )
    config.mark_setup_complete()


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
        console = Console()
        config = Config()
        if config.is_first_run:
            _run_first_time_setup(config, console)
        database = db.DatabaseConnection(config)
        random_number_source = create_entropy_source_factory(mode)
        vault = VaultSession(database, random_number_source, console)
        sesame_shell = SesameShell(vault, mode)
        sesame_shell.start()
    except KeyboardInterrupt:
        print("Sesame interrupted, clearing clipboard and exiting...bye byeee!")
        clear_clipboard()
        exit(0)


@app.command("config")
def config_command():
    console = Console()
    config = Config()
    keys = list(Config.configurable_keys.keys())

    console.print("[bold cyan]Sesame Configuration[/bold cyan]\n")
    for i, name in enumerate(keys, start=1):
        description = Config.configurable_keys[name]["description"]
        current_value = config.get_configurable_value(name)
        console.print(f"  [cyan]{i}.[/cyan] {name} - {description}")
        console.print(f"     current value: [yellow]{current_value}[/yellow]")

    choice = (
        console.input(
            f"\nWhich setting would you like to change? Enter the index: (1 to {len(keys)}, or 'q' to cancel): "
        )
        .strip()
        .lower()
    )
    if choice in ("q", "quit", ""):
        console.print("[dim]No changes made.[/dim]")
        return

    try:
        index = int(choice) - 1
        if index < 0 or index >= len(keys):
            raise ValueError
    except ValueError:
        console.print("[red]✘  Invalid choice.[/red]")
        return

    name = keys[index]
    raw_value = console.input(f"Enter new value for '{name}': ")
    if not raw_value.strip():
        console.print("[yellow]⚠  No value entered, nothing changed.[/yellow]")
        return

    new_value = raw_value.strip()
    if name == "db_path":
        new_value = _prepare_db_path(new_value)

    config.set_configurable_value(name, new_value)
    config.mark_setup_complete()
    console.print(f"[green]✔  '{name}' updated to:[/green] {new_value}")
