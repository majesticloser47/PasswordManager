from argon2 import PasswordHasher

from ..repository.auth import fetch_master_user, insert_master_user


def signup_master(username, password_str):
    ph = PasswordHasher()
    pass_hash = ph.hash(password_str)
    res = insert_master_user(username, pass_hash)
    if res:
        print("Master user created successfully")
    return res


def check_master_password(username, password_str):
    ph = PasswordHasher()
    master_user = fetch_master_user(username)
    if not master_user:
        print("Master user not found, signing up new user...")
        signup_master(username, password_str)
        return True
    stored_pass_hash = master_user["password_hash"] if master_user else None
    try:
        return ph.verify(stored_pass_hash, password_str)
    except Exception as e:
        print("Password verification failed:", e)
        return False
