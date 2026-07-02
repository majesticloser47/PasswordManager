import json
import os
import tkinter as tk

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from rich.console import Console

from ..repository.db import DatabaseConnection

db = DatabaseConnection()
console = Console()


def add_password_entry(service, username, notes, password, vault_key) -> bool:
    data = {
        "service": service,
        "username": username,
        "notes": notes,
        "password": password,
    }
    nonce = os.urandom(12)
    encrypted_data = AESGCM(vault_key).encrypt(nonce, json.dumps(data).encode(), None)
    return db.add_password_entry(encrypted_data, nonce)


def retrieve_pass_list(vault_key):
    encrypted_entries = db.get_all_password_entries()
    decrypted_entries = []
    for entry in encrypted_entries:
        entry_id = entry["id"]
        nonce = entry["nonce"]
        encrypted_data = entry["data"]
        decrypted_data = AESGCM(vault_key).decrypt(nonce, encrypted_data, None)
        decrypted_entries.append({"id": entry_id, **json.loads(decrypted_data)})
    return decrypted_entries


def get_password_entry_for_service(service: str, vault_key):
    entries = retrieve_pass_list(vault_key)
    for entry in entries:
        if entry["service"] == service:
            copy_pass_to_clipboard(entry["password"])


def delete_password_entry(service: str, vault_key):
    entries = retrieve_pass_list(vault_key)
    for entry in entries:
        if entry["service"] == service:
            prompt = input(
                f"Are you sure you want to delete the password entry for service '{service}'? (y/n): "
            )
            if prompt.lower() == "n" or prompt.lower() == "no":
                console.print("[yellow]⚠  Deletion cancelled.[/yellow]")
                return

            elif prompt.lower() == "y" or prompt.lower() == "yes":
                db.delete_password_entry(entry["id"])
                console.print(
                    f"[green]✔  Password entry for service '{service}' has been deleted.[/green]"
                )
                return

            else:
                console.print("[red]✘  Invalid input. Please enter 'y' or 'n'.[/red]")
                return
    console.print(
        f"[yellow]⚠  No password entry found for service '{service}'.[/yellow]"
    )


def copy_pass_to_clipboard(text):
    try:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        console.print(
            "[green]✔  Password copied to clipboard. It will be cleared in 20 seconds.[/green]"
        )
        root.after(
            20000,
            lambda: (
                root.clipboard_clear(),
                console.print("[yellow]⚠  Clipboard cleared.[/yellow]"),
                root.destroy(),
            ),
        )
        root.mainloop()
    except KeyboardInterrupt:
        root.clipboard_clear()
        print("Program interrupted, clearing clipboard")
        exit(0)
