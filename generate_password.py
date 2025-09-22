import secrets
import os
from argon2 import PasswordHasher
import getpass
from db import *
import tkinter as tk

def check_master_password(password_str):
    ph = PasswordHasher()
    # password is "thisisthepassword"
    stored_pass_hash = "$argon2id$v=19$m=65536,t=3,p=4$hCYtsVJUbfFiTK+ID6lVqQ$Q0/0L+8FCOutghB67QJ8KIFdjJFXoVH+LgVfF8/ON6w"
    new_pass_hash = ph.hash(password_str)
    try:
        return ph.verify(stored_pass_hash, password_str)
    except Exception as e:
        return False

# def create_pass_hash():
#     print("Enter master password: ")
#     password_str = input()
#     ph = PasswordHasher()
#     pass_hash = ph.hash(password_str)
#     print("Password hash created: ", pass_hash)
#     return pass_hash

def extract_passwords():
    res = init_db()
    return res

# def copy_pass_to_clipboard(id):
#     try:
#         pwd = fetch_password_by_id(id)
#         if pwd:
#             root = tk.Tk()
#             root.withdraw()
#             root.clipboard_clear()
#             root.clipboard_append(pwd)
#             root.update()
#             print("Password copied to clipboard. It will be cleared in 20 seconds.")
#             root.after(20000, lambda: (root.clipboard_clear(), print("Clipboard cleared"), root.destroy()))
#             root.mainloop()
#         else:
#             print("Password not found")
#     except KeyboardInterrupt:
#         root.clipboard_clear()
#         print("Program interrupted, clearing clipboard")
#         exit(0)

def access_manager(password_str):
    if check_master_password(password_str):
        print("Your passwords list: ")
        pwd_list = extract_passwords()
        print(pwd_list)
        print("Enter 'v' to view password, 'a' to add password, 'd' to delete password, 'q' to quit: ")
        choice = input()
        if choice == 'v':
            print("Enter the id of the password to view: ")
            pwd_id = str(input())
            if fetch_password_by_id(pwd_id):
                print("Password copied to clipboard")
            else:
                print("Password not found")
    else:
        print("Password verification failed")
        

password_str = getpass.getpass("Enter master password: ")
access_manager(password_str)
