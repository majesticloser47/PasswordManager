import tkinter as tk

from argon2 import PasswordHasher

from ..repository.db import fetch_password_by_id, init_db


def create_pass_hash():
    print("Enter master password: ")
    password_str = input()
    ph = PasswordHasher()
    pass_hash = ph.hash(password_str)
    print("Password hash created: ", pass_hash)
    return pass_hash


def extract_passwords():
    res = init_db()
    return res


def copy_pass_to_clipboard(id):
    try:
        pwd = fetch_password_by_id(id)
        if pwd:
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(pwd)
            root.update()
            print("Password copied to clipboard. It will be cleared in 20 seconds.")
            root.after(20000, lambda: (root.clipboard_clear(), print("Clipboard cleared"), root.destroy()))
            root.mainloop()
        else:
            print("Password not found")
    except KeyboardInterrupt:
        root.clipboard_clear()
        print("Program interrupted, clearing clipboard")
        exit(0)
