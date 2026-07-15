from sesame.service.entropy_sources.csprng import CryptographicRandomNumberSource
from sesame.service.entropy_sources.entropy_source import EntropySource
from sesame.service.entropy_sources.qrng import QuantumRandomNumberSource
from sesame.service.enum.entropy_sources_enum import EntropySourceEnum


def create_entropy_source_factory(source: EntropySource):
    match source:
        case EntropySourceEnum.QRNG:
            return QuantumRandomNumberSource()
        case EntropySourceEnum.CSPRNG:
            return CryptographicRandomNumberSource()
    raise ValueError(
        f"Unsupported entropy source type \"{source}\". Please choose either 'QRNG' or 'CSPRNG'"
    )
