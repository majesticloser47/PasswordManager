import cmd
import getpass
import os
import sys

from sesame.service.generate_password import generate_password
from sesame.service.password_actions import add_password_entry, copy_pass_to_clipboard
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

    def __init__(self, vault: VaultSession):
        super().__init__()
        self.vault = vault
        if not vault.unlocked:
            self.prompt = f"{_RED}closed sesame{_RESET} > "
        else:
            self.prompt = f"{_GREEN}open sesame{_RESET} > "

    def do_unlock(self, arg):
        master_password = getpass.getpass("Enter master password: ", stream=sys.stdout)
        try:
            self.vault.unlock(master_password)
            if self.vault.unlocked:
                print(f"{_GREEN}✔  Vault unlocked successfully.{_RESET}")
                self.prompt = f"{_GREEN}open sesame{_RESET} > "
        except Exception as e:
            print(f"{_RED}✘  Failed to unlock vault:{_RESET} {e}")

    def do_generate(self, arg):
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

    def do_lock(self, arg):
        if self.vault.unlocked:
            self.vault.lock()
            self.prompt = f"{_RED}closed sesame{_RESET} > "
        else:
            print(f"{_YELLOW}⚠  Vault is already locked.{_RESET}")

    def do_exit(self, arg):
        print(f"\n{_DIM}Exiting Sesame CLI. Byee byeeeeee!{_RESET}\n")
        return True

    def start(self):
        self.cmdloop()
