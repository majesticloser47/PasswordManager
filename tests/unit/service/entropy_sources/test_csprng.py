from sesame.service.entropy_sources import csprng
from sesame.service.entropy_sources.csprng import CryptographicRandomNumberSource
from sesame.service.entropy_sources.entropy_source import EntropySource


class TestCryptographicRandomNumberSource:
    def test_is_an_entropy_source(self):
        assert isinstance(CryptographicRandomNumberSource(), EntropySource)

    def test_delegates_to_secrets_randbelow(self, mocker):
        mocked = mocker.patch.object(csprng.secrets, "randbelow", return_value=7)
        source = CryptographicRandomNumberSource()

        result = source.randbelow(10)

        mocked.assert_called_once_with(10)
        assert result == 7

    def test_returned_value_is_always_within_bounds(self):
        source = CryptographicRandomNumberSource()
        for _ in range(200):
            value = source.randbelow(37)
            assert 0 <= value < 37

    def test_upper_bound_of_one_always_returns_zero(self):
        source = CryptographicRandomNumberSource()
        assert source.randbelow(1) == 0
