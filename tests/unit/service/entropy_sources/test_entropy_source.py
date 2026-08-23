import pytest

from sesame.service.entropy_sources.entropy_source import EntropySource


class _ConcreteSource(EntropySource):
    def randbelow(self, upper):
        return 0


class _SuperCallingSource(EntropySource):
    """Subclass that deliberately calls the abstract base implementation,
    letting us exercise (and cover) the NotImplementedError branch."""

    def randbelow(self, upper):
        return super().randbelow(upper)


class TestEntropySource:
    def test_cannot_instantiate_abstract_base_directly(self):
        with pytest.raises(TypeError):
            EntropySource()

    def test_subclass_without_randbelow_cannot_be_instantiated(self):
        class _Incomplete(EntropySource):
            pass

        with pytest.raises(TypeError):
            _Incomplete()

    def test_concrete_subclass_can_be_instantiated_and_used(self):
        source = _ConcreteSource()
        assert source.randbelow(10) == 0

    def test_base_randbelow_raises_not_implemented_error(self):
        source = _SuperCallingSource()
        with pytest.raises(NotImplementedError):
            source.randbelow(10)
