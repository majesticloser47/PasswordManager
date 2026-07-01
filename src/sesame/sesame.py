import cmd
import getpass
import os
import sys

from rich.console import Console
from rich.table import Table

from sesame.service.generate_password import generate_password
from sesame.service.password_actions import (
    add_password_entry,
    copy_pass_to_clipboard,
    delete_password_entry,
    get_password_entry_for_service,
    retrieve_pass_list,
)
from sesame.vault.vault import VaultSession

if os.name == "nt":
    os.system("")

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"


class SesameShell(cmd.Cmd):
    intro = (
        f"\n{_CYAN}{_BOLD}"
        "  ╔══════════════════════════════════════╗\n"
        "  ║      Sesame CLI Password Manager     ║\n"
        "  ║                v0.1.0                ║\n"
        "  ╚══════════════════════════════════════╝"
        f"{_RESET}\n"
    )

    console = Console()

    def __init__(self, vault: VaultSession):
        super().__init__()
        self.vault = vault
        if not vault.unlocked:
            self.prompt = f"{_RED}closed sesame{_RESET} > "
        else:
            self.prompt = f"{_GREEN}open sesame{_RESET} > "

    def do_unlock(self, _):
        master_password = getpass.getpass("Enter master password: ", stream=sys.stdout)
        try:
            self.vault.unlock(master_password)
            if self.vault.unlocked:
                print(f"{_GREEN}✔  Vault unlocked successfully.{_RESET}")
                self.prompt = f"{_GREEN}open sesame{_RESET} > "
        except Exception as e:
            print(f"{_RED}✘  Failed to unlock vault:{_RESET} {e}")

    def do_generate(self, _):
        if self.vault.unlocked:
            service = input(f"{_CYAN}  Service name  : {_RESET}")
            username = input(f"{_CYAN}  Username      : {_RESET}")
            notes = input(f"{_CYAN}  Notes (opt.)  : {_RESET}") or ""
            length = int(input(f"{_CYAN}  Password length: {_RESET}"))
            password = generate_password(length)

            add_password_entry(service, username, notes, password, self.vault.vault_key)
            copy_pass_to_clipboard(password)
        else:
            print(f"{_YELLOW}⚠  Vault is locked — please unlock it first.{_RESET}")

    def do_list(self, _):
        if self.vault.unlocked:
            entries = retrieve_pass_list(self.vault.vault_key)
            if entries:
                self.table = Table(show_header=True, title="Saved Passwords", header_style="bold magenta")
                self.table.add_column("Service", style="cyan")
                self.table.add_column("Username", style="green")
                self.table.add_column("Notes", style="yellow")
                self.table.add_column("Password", style="red")
                for entry in entries:
                    self.table.add_row(entry["service"], entry["username"], entry["notes"], "*" * 10)
                self.console.print(self.table)
            else:
                print(f"{_YELLOW}⚠  No password entries found.{_RESET}")
        else:
            print(f"{_YELLOW}⚠  Vault is locked — please unlock it first.{_RESET}")

    def do_fetch(self, arg):
        if self.vault.unlocked:
            service = arg.strip()
            if not service:
                print(f"{_YELLOW}⚠  Please provide a service name to fetch the password.{_RESET}")
                return
            get_password_entry_for_service(service, self.vault.vault_key)

    def do_delete(self, arg):
        if self.vault.unlocked:
            service = arg.strip()
            if not service:
                print(f"{_YELLOW}⚠  Please provide a service name to delete the password entry.{_RESET}")
                return
            delete_password_entry(service, self.vault.vault_key)
        else:
            print(f"{_YELLOW}⚠  Vault is locked — please unlock it first.{_RESET}")

    def do_lock(self, _):
        if self.vault.unlocked:
            self.vault.lock()
            self.prompt = f"{_RED}closed sesame{_RESET} > "
        else:
            print(f"{_YELLOW}⚠  Vault is already locked.{_RESET}")

    def do_exit(self, _):
        print(f"\n{_DIM}Exiting Sesame CLI. Byee byeeeeee!{_RESET}\n")
        return True

    def start(self):
        self.cmdloop()
