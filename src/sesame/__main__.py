from sesame.util.functions import clear_clipboard
from sesame.sesame import SesameShell
from sesame.vault.vault import VaultSession


def main():
    try:
        vault = VaultSession()  # Initialize the vault session
        sesame_shell = SesameShell(vault)
        sesame_shell.start()
    except KeyboardInterrupt:
        print("Sesame interrupted, clearing clipboard and exiting...bye byeee!")
        clear_clipboard()
        exit(0)


if __name__ == "__main__":
    main()
