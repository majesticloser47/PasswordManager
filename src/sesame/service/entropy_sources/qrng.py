import requests
from requests.exceptions import HTTPError
from collections import deque

from sesame.service.entropy_sources.csprng import CryptographicRandomNumberSource

from .entropy_source import EntropySource


class QuantumRandomNumberSource(EntropySource):
    def __init__(self):
        self._qubit_buffer = deque()
        self._fallback_source = CryptographicRandomNumberSource()

    def _get_qubit_pool_from_anu_api(self):
        self._qubit_pool_size = 1024
        try:
            res = requests.get(
                f"https://qrng.anu.edu.au/API/jsonI.php?length={self._qubit_pool_size}&type=uint8",
                timeout=(5, 10),
            )
            if res.status_code == 200:
                self._qubit_pool = res.json()["data"]
                return self._qubit_pool
            else:
                raise HTTPError(
                    "Failed to fetch qubit pool from ANU API.", response=res
                )
        except Exception as e:
            print(
                f"Error fetching qubit pool from ANU API: {e}. Falling back to CSPRNG."
            )
            return [
                self._fallback_source.randbelow(256)
                for _ in range(self._qubit_pool_size)
            ]

    def _refill(self):
        if not self._qubit_buffer:
            qubit_pool = self._get_qubit_pool_from_anu_api()
            self._qubit_buffer.extend(qubit_pool)

    def _randbits(self, k):
        bytes_needed = (k + 7) // 8
        while len(self._qubit_buffer) < bytes_needed:
            self._refill()
        bits = 0
        for _ in range(bytes_needed):
            bits = (bits << 8) | self._qubit_buffer.popleft()
        bits &= (1 << k) - 1
        return bits

    def randbelow(self, upper):
        bits_needed = (upper - 1).bit_length()
        while True:
            idx = self._randbits(bits_needed)
            if idx < upper:
                return idx
