from enum import Enum


class EntropySourceEnum(Enum):
    CSPRNG = "normal"
    QRNG = "quantum"
