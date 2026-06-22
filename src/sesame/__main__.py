from .service.auth_service import check_master_password
from .service.generate_password import generate_password
from .service.password_actions import copy_pass_to_clipboard


def main():
    username = input("Enter master username: ")
    password = input("Enter master password: ")
    if check_master_password(username, password):
        print("Access granted")
        inp = input("Enter 'g' to generate a password for a user and copy it to clipboard: ")
        if inp.lower() == "g":
            length = int(input("Enter desired password length: "))
            hashed_password = generate_password(length)
            copy_pass_to_clipboard(hashed_password)
    else:
        print("Access denied")


if __name__ == "__main__":
    main()
