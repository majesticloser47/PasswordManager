from sesame.vault.vault import VaultSession

from .service.generate_password import generate_password
from .service.password_actions import add_password_entry, copy_pass_to_clipboard


def main():
    vault = VaultSession()  # Initialize the vault session
    master_password = input("Enter master password: ")
    if vault.unlock(master_password):
        print("Access granted")
        inp = input("Enter 'g' to generate a password for a service: ")
        if inp.lower() == "g":
            service = input("Enter service name for which to generate password: ")
            username = input("Enter username for which to generate password: ")
            notes = input("Enter any notes for this password (optional): ") or ""
            length = int(input("Enter desired password length: "))
            password = generate_password(length)

            add_password_entry(service, username, notes, password, vault.vault_key)
            copy_pass_to_clipboard(password)
    else:
        print("Access denied")


if __name__ == "__main__":
    main()
