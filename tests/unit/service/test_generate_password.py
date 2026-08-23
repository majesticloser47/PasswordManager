import string

from sesame.service.enum.entropy_sources_enum import EntropySourceEnum
from sesame.service.generate_password import ALPHABET, PasswordGenerator
from tests.helpers import FakeEntropySource


class TestAlphabet:
    def test_alphabet_contains_letters_digits_and_punctuation(self):
        assert set(string.ascii_letters) <= set(ALPHABET)
        assert set(string.digits) <= set(ALPHABET)
        assert set(string.punctuation) <= set(ALPHABET)


class TestPasswordGeneratorDefaults:
    def test_default_length_is_eight(self):
        generator = PasswordGenerator(entropy=EntropySourceEnum.CSPRNG)
        password = generator.generate_password()
        assert len(password) == 8

    def test_custom_length_is_respected(self):
        generator = PasswordGenerator(entropy=EntropySourceEnum.CSPRNG)
        password = generator.generate_password(24)
        assert len(password) == 24

    def test_zero_length_returns_empty_string(self):
        generator = PasswordGenerator(entropy=EntropySourceEnum.CSPRNG)
        assert generator.generate_password(0) == ""

    def test_negative_length_returns_empty_string(self):
        generator = PasswordGenerator(entropy=EntropySourceEnum.CSPRNG)
        assert generator.generate_password(-5) == ""

    def test_all_characters_come_from_alphabet(self):
        generator = PasswordGenerator(entropy=EntropySourceEnum.CSPRNG)
        password = generator.generate_password(200)
        assert all(char in ALPHABET for char in password)

    def test_qrng_mode_constructs_quantum_entropy_source(self):
        from sesame.service.entropy_sources.qrng import QuantumRandomNumberSource

        generator = PasswordGenerator(entropy=EntropySourceEnum.QRNG)
        assert isinstance(generator.entropy_source, QuantumRandomNumberSource)


class TestPasswordGeneratorDeterministic:
    def test_generated_password_matches_expected_indices(self):
        generator = PasswordGenerator(entropy=EntropySourceEnum.CSPRNG)
        generator.entropy_source = FakeEntropySource([0, 1, 2])

        password = generator.generate_password(3)

        assert password == ALPHABET[0] + ALPHABET[1] + ALPHABET[2]

    def test_entropy_source_queried_once_per_character(self):
        generator = PasswordGenerator(entropy=EntropySourceEnum.CSPRNG)
        fake = FakeEntropySource([0])
        generator.entropy_source = fake

        generator.generate_password(10)

        assert len(fake.calls) == 10
        assert all(call == len(ALPHABET) for call in fake.calls)
