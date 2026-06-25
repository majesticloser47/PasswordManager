import cmd

from sesame.service.generate_password import generate_password
from sesame.service.password_actions import add_password_entry, copy_pass_to_clipboard
from sesame.vault.vault import VaultSession


class SesameShell(cmd.Cmd):
    intro = "Sesame CLI Password Manager v1.0"

    def __init__(self, vault: VaultSession):
        super().__init__()
        self.vault = vault
        if not vault.unlocked:
            self.prompt = "closed sesame > "
        else:
            self.prompt = "open sesame > "

    def do_unlock(self, arg):
        master_password = input("Enter master password: ")
        try:
            self.vault.unlock(master_password)
            if self.vault.unlocked:
                print("Vault unlocked successfully.")
                self.prompt = "open sesame > "
        except Exception as e:
            print("Failed to unlock vault:", e)

    def do_generate(self, arg):
        if self.vault.unlocked:
            service = input("Enter service name for which to generate password: ")
            username = input("Enter username for which to generate password: ")
            notes = input("Enter any notes for this password (optional): ") or ""
            length = int(input("Enter desired password length: "))
            password = generate_password(length)

            add_password_entry(service, username, notes, password, self.vault.vault_key)
            copy_pass_to_clipboard(password)

    def do_lock(self, arg):
        if self.vault.unlocked:
            self.vault.lock()
            self.prompt = "closed sesame > "
        else:
            print("Vault is already locked.")

    def start(self):
        print(self.intro)
        self.cmdloop()
