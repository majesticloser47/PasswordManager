import cmd
import getpass
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from setuptools_scm import get_version

from sesame.service.generate_password import generate_password
from sesame.service.password_actions import (
    add_password_entry,
    copy_pass_to_clipboard,
    delete_password_entry,
    get_password_entry_for_service,
    retrieve_pass_list,
)
from sesame.vault.vault import VaultSession


class SesameShell(cmd.Cmd):
    intro = None
    console = Console()

    def __init__(self, vault: VaultSession):
        super().__init__()
        self.vault = vault
        self.prompt = self._render_prompt("[red]closed sesame[/red]")
        self.vault_locked_message = (
            "[yellow]⚠  Vault is locked — please unlock it first.[/yellow]"
        )

    def _render_prompt(self, markup: str) -> str:
        """Render Rich markup to an ANSI string suitable for cmd.Cmd prompt."""
        with self.console.capture() as cap:
            self.console.print(markup, end="")
        return cap.get() + " > "

    def do_unlock(self, _):
        master_password = getpass.getpass("Enter master password: ", stream=sys.stdout)
        try:
            self.vault.unlock(master_password)
            if self.vault.unlocked:
                self.console.print("[green]✔  Vault unlocked successfully.[/green]")
                self.prompt = self._render_prompt("[green]open sesame[/green]")
        except Exception as e:
            self.console.print(f"[red]✘  Failed to unlock vault:[/red] {e}")

    def do_generate(self, _):
        if self.vault.unlocked:
            service = self.console.input("[cyan]  Service name   : [/cyan]")
            username = self.console.input("[cyan]  Username       : [/cyan]")
            notes = self.console.input("[cyan]  Notes (opt.)   : [/cyan]") or ""
            length = int(self.console.input("[cyan]  Password length: [/cyan]"))
            password = generate_password(length)
            add_password_entry(service, username, notes, password, self.vault.vault_key)
            copy_pass_to_clipboard(password)
        else:
            self.console.print(self.vault_locked_message)

    def do_list(self, _):
        if self.vault.unlocked:
            entries = retrieve_pass_list(self.vault.vault_key)
            if entries:
                table = Table(
                    show_header=True,
                    title="Saved Passwords",
                    header_style="bold magenta",
                )
                table.add_column("Service", style="cyan")
                table.add_column("Username", style="green")
                table.add_column("Notes", style="yellow")
                table.add_column("Password", style="red")
                for entry in entries:
                    table.add_row(
                        entry["service"], entry["username"], entry["notes"], "*" * 10
                    )
                self.console.print(table)
            else:
                self.console.print("[yellow]⚠  No password entries found.[/yellow]")
        else:
            self.console.print(self.vault_locked_message)

    def do_fetch(self, arg):
        if self.vault.unlocked:
            service = arg.strip()
            if not service:
                self.console.print("[yellow]⚠  Please provide a service name.[/yellow]")
                return
            get_password_entry_for_service(service, self.vault.vault_key)

    def do_delete(self, arg):
        if self.vault.unlocked:
            service = arg.strip()
            if not service:
                self.console.print("[yellow]⚠  Please provide a service name.[/yellow]")
                return
            delete_password_entry(service, self.vault.vault_key)
        else:
            self.console.print(self.vault_locked_message)

    def do_lock(self, _):
        if self.vault.unlocked:
            self.vault.lock()
            self.prompt = self._render_prompt("[red]closed sesame[/red]")
        else:
            self.console.print("[yellow]⚠  Vault is already locked.[/yellow]")

    def do_exit(self, _):
        self.console.print("\n[dim]Exiting Sesame CLI. Byee byeeeeee![/dim]\n")
        return True

    def start(self):
        self.console.print(
            Panel(
                f"[bold]Sesame CLI Password Manager[/bold]\n[dim]v{get_version()}[/dim]",
                style="cyan",
                padding=(1, 6),
            )
        )
        self.cmdloop()
