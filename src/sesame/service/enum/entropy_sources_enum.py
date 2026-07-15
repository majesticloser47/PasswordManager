from enum import Enum


class EntropySourceEnum(Enum):
    CSPRNG = "CSPRNG"
    QRNG = "QRNG"
