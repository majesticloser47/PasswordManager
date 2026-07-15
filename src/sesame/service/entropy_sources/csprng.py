import secrets

from .entropy_source import EntropySource


class CryptographicRandomNumberSource(EntropySource):
    def randbelow(self, upper):
        return secrets.randbelow(upper)
