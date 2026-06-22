import secrets
import string

import requests
from argon2 import PasswordHasher

from ..config import Config
from .qrng import get_qrng_sim_value


def get_qrng_salt():
    if Config.ENV == "development":
        return get_qrng_sim_value()
    response = requests.get("https://qrng.anu.edu.au/API/jsonI.php?length=16&type=hex16")
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            return data["data"][0]
    raise KeyError("Failed to get salt from QRNG service.")


def generate_password(length=16):
    salt = get_qrng_salt()
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    if salt:
        password = "".join(secrets.choice(chars) for _ in range(length))
        pass_hash = PasswordHasher().hash(password + salt)
        return pass_hash
    else:
        raise ValueError("Salt is None, cannot generate password.")
