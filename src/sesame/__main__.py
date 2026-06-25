from sesame.sesame import SesameShell
from sesame.vault.vault import VaultSession


def main():
    vault = VaultSession()  # Initialize the vault session
    sesame_shell = SesameShell(vault)
    sesame_shell.start()


if __name__ == "__main__":
    main()
