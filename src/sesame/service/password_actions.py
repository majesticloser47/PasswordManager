import json
import os
import tkinter as tk

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..repository.db import DatabaseConnection

db = DatabaseConnection()


def add_password_entry(service, username, notes, password, vault_key) -> bool:
    data = {"service": service, "username": username, "notes": notes, "password": password}
    nonce = os.urandom(12)
    encrypted_data = AESGCM(vault_key).encrypt(nonce, json.dumps(data).encode(), None)
    return db.add_password_entry(encrypted_data, nonce)


def retrieve_pass_list(vault_key):
    encrypted_entries = db.get_all_password_entries()
    decrypted_entries = []
    for entry in encrypted_entries:
        nonce = entry["nonce"]
        encrypted_data = entry["data"]
        decrypted_data = AESGCM(vault_key).decrypt(nonce, encrypted_data, None)
        decrypted_entries.append(json.loads(decrypted_data))
    return decrypted_entries


def get_password_entry_for_service(service: str, vault_key):
    entries = retrieve_pass_list(vault_key)
    for entry in entries:
        if entry["service"] == service:
            copy_pass_to_clipboard(entry["password"])


def copy_pass_to_clipboard(text):
    try:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        print("Password copied to clipboard. It will be cleared in 20 seconds.")
        root.after(20000, lambda: (root.clipboard_clear(), print("Clipboard cleared"), root.destroy()))
        root.mainloop()
    except KeyboardInterrupt:
        root.clipboard_clear()
        print("Program interrupted, clearing clipboard")
        exit(0)
