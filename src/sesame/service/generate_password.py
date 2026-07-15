import string

from .entropy_sources.entropy_factory import create_entropy_source_factory
from ..service.enum.entropy_sources_enum import EntropySourceEnum

ALPHABET = string.ascii_letters + string.digits + string.punctuation
max_idx = len(ALPHABET)


class PasswordGenerator:
    def __init__(self, entropy: EntropySourceEnum):
        self.entropy_source = create_entropy_source_factory(entropy)

    def generate_password(self, length=8):
        pass_chars = []
        for _ in range(length):
            idx = self.entropy_source.randbelow(max_idx)
            pass_chars.append(ALPHABET[idx])
        password = "".join(pass_chars)
        return password
