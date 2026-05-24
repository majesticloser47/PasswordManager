from .service.auth_service import check_master_password


def main():
    username = input("Enter master username: ")
    password = input("Enter master password: ")
    if check_master_password(username, password):
        print("Access granted")
    else:
        print("Access denied")


if __name__ == "__main__":
    main()
