import pytest

from sesame.service.entropy_sources.csprng import CryptographicRandomNumberSource
from sesame.service.entropy_sources.entropy_factory import create_entropy_source_factory
from sesame.service.entropy_sources.qrng import QuantumRandomNumberSource
from sesame.service.enum.entropy_sources_enum import EntropySourceEnum


class TestCreateEntropySourceFactory:
    def test_csprng_enum_returns_cryptographic_source(self):
        source = create_entropy_source_factory(EntropySourceEnum.CSPRNG)
        assert isinstance(source, CryptographicRandomNumberSource)

    def test_qrng_enum_returns_quantum_source(self):
        source = create_entropy_source_factory(EntropySourceEnum.QRNG)
        assert isinstance(source, QuantumRandomNumberSource)

    def test_unsupported_value_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported entropy source type"):
            create_entropy_source_factory("invalid-source")

    def test_none_raises_value_error(self):
        with pytest.raises(ValueError):
            create_entropy_source_factory(None)
