from abc import ABC, abstractmethod


class EntropySource(ABC):
    @abstractmethod
    def randbelow(self, upper):
        raise NotImplementedError("randbelow method must be implemented by subclasses.")
