import string

from ..config import Config
from .qrng import QRNG

ALPHABET = string.ascii_letters + string.digits + string.punctuation
max_idx = len(ALPHABET)


def rand_int_below_max_idx(max_idx):
    bits_needed = (max_idx - 1).bit_length()
    if Config.ENV == "development":
        while True:
            bits = QRNG().get_qrng_sim_rand_bits(bits_needed)
            idx = int(bits, 2)
            if idx < max_idx:
                return idx
    # add else here: for production, get random number from actual qrng like ANU


def generate_password(length=16):
    pass_chars = []
    for _ in range(length):
        idx = rand_int_below_max_idx(max_idx)
        pass_chars.append(ALPHABET[idx])
    password = "".join(pass_chars)
    return password
