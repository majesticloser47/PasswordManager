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
