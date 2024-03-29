from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Unigram:
    id: str | int
    word: str
    count: int = 0


@dataclass
class Bigrams:
    id: str | int
    count: int
    counts: dict[str | int, int]
    words: dict[str | int, float]


class ABCRepo(ABC):


    @abstractmethod
    def addUnigrams(self, unigrams: list[tuple[str, int]]):  # pragma: no cover
        ...
    
    @abstractmethod
    def getAllUnigrams(self) -> list[tuple[str, int]]: # pragma: no cover
        ...

    @abstractmethod
    def addBigrams(self, bigrams: list[tuple[str, str, int]], limit: int = 10000):  # pragma: no cover
        ...

    @abstractmethod
    def getAllBigrams(self) -> list[tuple[str, str, int]]: # pragma: no cover
        ...

    @abstractmethod
    def getUnigrams(self, ids: list[str | int], limit: int = None) -> list[Unigram | None]:  # pragma: no cover
        ...

    @abstractmethod
    def getUnigramsByWords(self, words: list[str]) -> list[Unigram | None]:  # pragma: no cover
        ...

    @abstractmethod
    def getForwardBigrams(self, id: str | int) -> Bigrams | None:  # pragma: no cover
        ...

    @abstractmethod
    def getBackwardBigrams(self, id: str | int) -> Bigrams | None:  # pragma: no cover
        ...

    @abstractmethod
    def matchPrefix(self, prefix: str, limit: int = 100) -> list[str | int]:  # pragma: no cover
        ...

    @abstractmethod
    def matchFuzzy(self, word: str, limit: int = 100, additionalIds: list[str | int] = []) -> dict[str | int, float]:  # pragma: no cover
        ...

