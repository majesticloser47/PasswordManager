import secrets
import os
from argon2 import PasswordHasher
import getpass
from db import init_db

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

def access_manager(password_str):
    if check_master_password(password_str):
        print("Your passwords list: ")
        pwd_list = extract_passwords()
        print(pwd_list)
        print("Enter 'v' to view password, 'a' to add password, 'd' to delete password, 'q' to quit: ")
        choice = input()
        if choice == 'v':
            print("Enter the id of the password to view: ")
            pwd_id = int(input())
            for pwd in pwd_list:
                if pwd[0] == pwd_id:
                    print("Copying password to clipboard")
                    # TODO: copy to clipboard
                    break
            else:
                print("Password id not found")
    else:
        print("Password verification failed")
        

password_str = getpass.getpass("Enter master password: ")
access_manager(password_str)
