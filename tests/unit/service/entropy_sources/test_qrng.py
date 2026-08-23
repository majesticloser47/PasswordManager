from collections import deque
import requests

from sesame.service.entropy_sources import qrng as qrng_module
from sesame.service.entropy_sources.qrng import QuantumRandomNumberSource


def _fake_response(status_code=200, data=None):
    class _Resp:
        def __init__(self):
            self.status_code = status_code

        def json(self):
            return {"data": data if data is not None else []}

    return _Resp()


class TestGetQubitPoolFromAnuApi:
    def test_success_returns_data_from_api(self, mocker):
        expected = list(range(1024))
        mocker.patch.object(
            qrng_module.requests, "get", return_value=_fake_response(200, expected)
        )
        source = QuantumRandomNumberSource()

        pool = source._get_qubit_pool_from_anu_api()

        assert pool == expected

    def test_non_200_status_falls_back_to_csprng(self, mocker):
        mocker.patch.object(
            qrng_module.requests, "get", return_value=_fake_response(500)
        )
        source = QuantumRandomNumberSource()

        pool = source._get_qubit_pool_from_anu_api()

        assert len(pool) == 1024
        assert all(isinstance(b, int) and 0 <= b < 256 for b in pool)

    def test_network_exception_falls_back_to_csprng(self, mocker):
        mocker.patch.object(
            qrng_module.requests,
            "get",
            side_effect=requests.exceptions.ConnectionError("boom"),
        )
        source = QuantumRandomNumberSource()

        pool = source._get_qubit_pool_from_anu_api()

        assert len(pool) == 1024
        assert all(isinstance(b, int) and 0 <= b < 256 for b in pool)

    def test_request_is_sent_with_expected_url_params(self, mocker):
        mocked_get = mocker.patch.object(
            qrng_module.requests, "get", return_value=_fake_response(200, [1, 2, 3])
        )
        source = QuantumRandomNumberSource()

        source._get_qubit_pool_from_anu_api()

        called_url = mocked_get.call_args[0][0]
        assert "length=1024" in called_url
        assert "type=uint8" in called_url


class TestRefill:
    def test_refill_populates_empty_buffer(self, mocker):
        source = QuantumRandomNumberSource()
        mocker.patch.object(
            source, "_get_qubit_pool_from_anu_api", return_value=[1, 2, 3]
        )

        source._refill()

        assert list(source._qubit_buffer) == [1, 2, 3]

    def test_refill_does_nothing_when_buffer_not_empty(self, mocker):
        source = QuantumRandomNumberSource()
        source._qubit_buffer = deque([9])
        fetch = mocker.patch.object(source, "_get_qubit_pool_from_anu_api")

        source._refill()

        fetch.assert_not_called()
        assert list(source._qubit_buffer) == [9]


class TestRandbits:
    def test_randbits_packs_bytes_big_endian_and_masks(self):
        source = QuantumRandomNumberSource()
        # 0b00000111 (7) then 0b00000010 (2) -> combined 0x0702, masked to 9 bits
        source._qubit_buffer = deque([7, 2])

        result = source._randbits(9)

        combined = (7 << 8) | 2
        assert result == combined & ((1 << 9) - 1)

    def test_randbits_consumes_required_bytes_from_buffer(self):
        source = QuantumRandomNumberSource()
        source._qubit_buffer = deque([1, 2, 3])

        source._randbits(8)  # needs exactly 1 byte

        assert list(source._qubit_buffer) == [2, 3]

    def test_randbits_triggers_refill_when_buffer_insufficient(self, mocker):
        source = QuantumRandomNumberSource()
        source._qubit_buffer = deque()
        mocker.patch.object(source, "_get_qubit_pool_from_anu_api", return_value=[42])

        result = source._randbits(8)

        assert result == 42


class TestRandbelow:
    def test_accepts_first_value_when_within_range(self):
        source = QuantumRandomNumberSource()
        # bits_needed for upper=5 -> (5-1).bit_length() == 3
        source._qubit_buffer = deque([2])  # 0b010 -> 2, within [0, 5)

        assert source.randbelow(5) == 2

    def test_rejects_out_of_range_values_and_retries(self):
        source = QuantumRandomNumberSource()
        # First byte masked to 3 bits -> 7 (rejected, >= upper=5).
        # Second byte masked to 3 bits -> 2 (accepted).
        source._qubit_buffer = deque([7, 2])

        assert source.randbelow(5) == 2

    def test_randbelow_result_always_within_bounds(self, mocker):
        source = QuantumRandomNumberSource()
        mocker.patch.object(
            source,
            "_get_qubit_pool_from_anu_api",
            return_value=list(range(256)) * 4,
        )

        for _ in range(50):
            value = source.randbelow(37)
            assert 0 <= value < 37
