from __future__ import annotations

from sesame.service.entropy_sources.entropy_source import EntropySource


class FakeEntropySource(EntropySource):
    """Deterministic stand-in for a real entropy source.

    Cycles through a fixed sequence of values (reduced modulo ``upper``)
    instead of relying on real randomness, so tests can assert on exact
    output.
    """

    def __init__(self, values: list[int] | None = None):
        self.values = list(values) if values is not None else [0]
        self.calls: list[int] = []
        self._index = 0

    def randbelow(self, upper: int) -> int:
        self.calls.append(upper)
        value = self.values[self._index % len(self.values)] % upper
        self._index += 1
        return value
