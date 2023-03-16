from abc import ABC
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
	words: dict[str | int, float]


class ABCRepo(ABC):

	def close(self):
		...

	def getUnigrams(self, ids: list[str | int], limit: int = 100) -> list[Unigram | None]:
		...

	def findWords(self, words: list[str]) -> list[Unigram | None]:
		...

	def getForwardBigrams(self, id:str | int) -> Bigrams:
		...
	
	def getBackwardBigrams(self, id:str | int) -> Bigrams:
		...

	def matchWords(self, prefix: str, limit: int = 100) -> list[str|int]:
		...

	def matchFuzzyWords(self, word: str, limit: int = 100, additionalIds: list[str|int] = []) -> list[str|int]:
		...