import tkinter as tk

from ..repository.db import DatabaseConnection

db = DatabaseConnection()


def extract_passwords():
    res = db.init_db()
    return res


def copy_pass_to_clipboard(id):
    try:
        pwd = db.fetch_password_by_id(id)
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
