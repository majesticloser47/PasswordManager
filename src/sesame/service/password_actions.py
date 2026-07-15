import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from rich.console import Console
from rich.table import Table
from sesame.util.functions import copy_pass_to_clipboard
from ..repository.db import DatabaseConnection

console = Console()
_db: DatabaseConnection | None = None


def _get_db() -> DatabaseConnection:
    global _db
    if _db is None:
        _db = DatabaseConnection()
    return _db


def add_password_entry(service, username, notes, password, vault_key) -> bool:
    data = {
        "service": service,
        "username": username,
        "notes": notes,
        "password": password,
    }
    nonce = os.urandom(12)
    encrypted_data = AESGCM(vault_key).encrypt(nonce, json.dumps(data).encode(), None)
    return _get_db().add_password_entry(encrypted_data, nonce)


def retrieve_pass_list(vault_key):
    encrypted_entries = _get_db().get_all_password_entries()
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
    entries_found = [entry for entry in entries if entry["service"] == service]
    if len(entries_found) == 0:
        console.print("[yellow]⚠  No password entries found.[/yellow]")
        return None
    if len(entries_found) > 1:
        console.print(
            "[yellow]⚠  Multiple password entries found. Please specify the number (1, 2, ...)[/yellow]"
        )
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=6)
        table.add_column("Service")
        table.add_column("Username")
        table.add_column("Notes")
        for i, entry in enumerate(entries_found):
            table.add_row(
                str(i + 1), entry["service"], entry["username"], entry["notes"]
            )
        console.print(table)
        choice = console.input("Your choice: ")
        copy_pass_to_clipboard(entries_found[int(choice) - 1]["password"])
    else:
        copy_pass_to_clipboard(entries_found[0]["password"])
        return None


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
                _get_db().delete_password_entry(entry["id"])
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
