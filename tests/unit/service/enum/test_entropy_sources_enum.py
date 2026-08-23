from sesame.service.enum.entropy_sources_enum import EntropySourceEnum


class TestEntropySourceEnum:
    def test_has_csprng_member_with_expected_value(self):
        assert EntropySourceEnum.CSPRNG.value == "normal"

    def test_has_qrng_member_with_expected_value(self):
        assert EntropySourceEnum.QRNG.value == "quantum"

    def test_contains_exactly_two_members(self):
        assert len(list(EntropySourceEnum)) == 2

    def test_members_are_distinct(self):
        assert EntropySourceEnum.CSPRNG != EntropySourceEnum.QRNG

    def test_lookup_member_by_value(self):
        assert EntropySourceEnum("normal") is EntropySourceEnum.CSPRNG
        assert EntropySourceEnum("quantum") is EntropySourceEnum.QRNG

    def test_lookup_with_invalid_value_raises_value_error(self):
        import pytest

        with pytest.raises(ValueError):
            EntropySourceEnum("not-a-real-value")
