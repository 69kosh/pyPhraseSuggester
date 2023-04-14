from .abcRepo import *
from rapidfuzz import *
import csv

class MemoRepo(ABCRepo):
	def __init__(self) -> None:
		super().__init__()

		self._unigrams = {}
		self._word2Id = {}
		self._prefix32Id = {}
		self._prefix22Id = {}
		self._prefix12Id = {}
		self._forwardBi = {}
		self._backwardBi = {}
		self._fuzzyIndex = {}

		# self.addUnigrams(unigrams)
		# self.addBigrams(bigrams, bigramsLimit)

	def addUnigrams(self, unigrams: list[tuple[str, int]]):

		keys1, keys2, keys3 = (set(), set(), set())

		seqId: int = max(0, len(self._unigrams))
		for uni in unigrams:
			word = str(uni[0])
			cnt = int(uni[1])
			if word in self._word2Id:
				id = self._word2Id[word]
				self._unigrams[id].count += cnt
			else:
				id = seqId
				self._unigrams[id] = Unigram(id, word, cnt)
				seqId += 1
				self._word2Id[word] = id

			key1 = word[0:1]
			if key1 not in self._prefix12Id:
				self._prefix12Id[key1] = {}
			if id in self._prefix12Id[key1]:
				self._prefix12Id[key1][id] += cnt
			else:
				self._prefix12Id[key1][id] = cnt

			keys1.add(key1)

			if len(word) > 1:
				key2 = word[0:2]
				if key2 not in self._prefix22Id:
					self._prefix22Id[key2] = {}
				if id in self._prefix22Id[key2]:
					self._prefix22Id[key2][id] += cnt
				else:
					self._prefix22Id[key2][id] = cnt

				keys2.add(key2)

			if len(word) > 2:
				key3 = word[0:3]
				if key3 not in self._prefix32Id:
					self._prefix32Id[key3] = {}
				if id in self._prefix32Id[key3]:
					self._prefix32Id[key3][id] += cnt
				else:
					self._prefix32Id[key3][id] = cnt

				keys3.add(key3)

		# sort all unigrams, and touched prefixes
		self._unigrams = dict(sorted(
			self._unigrams.items(), key=lambda x: x[1].count, reverse=True))

		for key in keys1:
			self._prefix12Id[key] = dict(
				sorted(self._prefix12Id[key].items(), key=lambda x: x[1], reverse=True))

		for key in keys2:
			self._prefix22Id[key] = dict(
				sorted(self._prefix22Id[key].items(), key=lambda x: x[1], reverse=True))

		for key in keys3:
			self._prefix32Id[key] = dict(
				sorted(self._prefix32Id[key].items(), key=lambda x: x[1], reverse=True))

		self.prepareFuzzyIndex()

	def addBigrams(self, bigrams: list[tuple[str, str, int]], limit: int = 10000):

		for bi in bigrams:
			fromId = self._word2Id[str(bi[0])]
			toId = self._word2Id[str(bi[1])]
			count = int(bi[2])

			if fromId not in self._forwardBi:
				self._forwardBi[fromId] = Bigrams(
					id=fromId, count=count, counts={toId: count}, words={})
			else:
				self._forwardBi[fromId].count += count
				if len(self._forwardBi[fromId].counts) < limit:
					self._forwardBi[fromId].counts[toId] = count

			if toId not in self._backwardBi:
				self._backwardBi[toId] = Bigrams(
					id=toId, count=count, counts={fromId: count}, words={})
			else:
				self._backwardBi[toId].count += count
				if len(self._backwardBi[toId].counts) < limit:
					self._backwardBi[toId].counts[fromId] = count

		for id in self._forwardBi:
			for id2 in self._forwardBi[id].counts:
				self._forwardBi[id].words[id2] = (self._forwardBi[id].counts[id2]
												  / self._forwardBi[id].count)

		for id in self._backwardBi:
			for id2 in self._backwardBi[id].counts:
				self._backwardBi[id].words[id2] = (self._backwardBi[id].counts[id2]
												   / self._forwardBi[id2].count)

	def prepareFuzzyIndex(self):
		self._fuzzyIndex = {}
		# для каждой униграмы разбиваем её на триграмы (может хватит би?)
		# и добавляем в словарь по ключу=триграмме ид униграмы
		# чтобы потом разбив слово на триграмы найти списки униграмы содержащих хотя бы одну из них
		# таким образом будем отсекать остальные слова из нечеткого поиска
		for uni in self._unigrams.values():
			if len(uni.word) < 3:
				continue
			for i in range(0, len(uni.word)-2, 1):
				tri = uni.word[i:i+3]
				if tri not in self._fuzzyIndex:
					self._fuzzyIndex[tri] = []
				self._fuzzyIndex[tri].append(uni.id)

	def getUnigrams(self, ids: list[str | int], limit: int = None) -> list[Unigram | None]:
		max = len(self._unigrams)
		limit = max if limit is None else limit
		return [self._unigrams[id] if id < max else None for id in ids[0:limit]]

	def getUnigramsByWords(self, words: list[str]) -> list[Unigram | None]:
		res = []
		for word in words:
			if word in self._word2Id:
				res.append(self._unigrams[self._word2Id[word]])
			else:
				res.append(None)
		return res

	def matchPrefix(self, prefix: str, limit: int = 100) -> list[str | int]:
		ids = []
		if len(prefix) > 2:
			if prefix[0:3] not in self._prefix32Id:
				return []
			if len(prefix) == 3:
				ids = list(self._prefix32Id[prefix[0:3]].keys())
			else:
				for id in self._prefix32Id[prefix[0:3]].keys():
					uni = self._unigrams[id]
					if uni.word.find(prefix) == 0:
						ids.append(id)
		elif len(prefix) == 2:
			if prefix not in self._prefix22Id:
				return []
			ids = list(self._prefix22Id[prefix].keys())
		elif len(prefix) == 1:
			if prefix not in self._prefix12Id:
				return []
			ids = list(self._prefix12Id[prefix].keys())
		else:
			for uni in self._unigrams.values():
				ids.append(uni.id)
				if len(ids) == limit:
					break

		return ids[0:limit]

	def getForwardBigrams(self, id: str | int) -> Bigrams | None:
		if id in self._forwardBi:
			return self._forwardBi[id]

	def getBackwardBigrams(self, id: str | int) -> Bigrams | None:
		if id in self._backwardBi:
			return self._backwardBi[id]

	def matchFuzzy(self, word: str, limit: int = 100, additionalIds: list[str | int] = []) -> dict[str | int, float]:
		'''Для слов которые не нашли четко, подбираем близкие варианты
				Для этого используем сравнение по левенштейну, 
				а чтобы не перебирать все слова, бьем слово на триграмы и ищем 
				подходящие слова, с включением хотя бы 50% этих грам по индексу триграм
						https://pypi.org/project/rapidfuzz/'''

		# если фраза короткая - ищем по префиксу
		# ids = []
		# if len(word) < 5:
		ids = self.matchPrefix(prefix=word, limit=limit) + additionalIds
		# print(ids)
		# разбиваем на триграммы
		lists = {}
		all = []
		for i in range(0, len(word)-2, 1):
			tri = word[i:i+3]
			if tri in self._fuzzyIndex:
				lists[tri] = set(self._fuzzyIndex[tri])
				all += lists[tri]
			else:
				lists[tri] = set()

		# составляем общий список, и считаем сколько пересечений (включений)
		# для каждого элемента
		counts = {}
		all = set(all)
		for tri in lists:
			inter = list(all & lists[tri])
			for id in inter:
				if id not in counts:
					counts[id] = 0
				counts[id] += 1

		l = (len(word)-2) // 2  # половина токинов
		for id in counts:
			if counts[id] >= l:
				ids.append(id)

		# print(ids)
		unis = self.getUnigrams(list(set(ids)))
		ratios = {}
		for uni in unis:
			ratios[uni.id] = (fuzz.ratio(word, uni.word) + 10.0)/110.0
			# print(word, uni.word, ratios[uni.id])

		# сортируем и подрезаем, делаем словарь
		return dict(sorted(ratios.items(), key=lambda item: item[1], reverse=True)[0:limit])

	def getAllUnigrams(self) -> list[tuple[str, int]]:
		for uni in list(self._unigrams.values()):
			yield (uni.word, uni.count)

	def getAllBigrams(self) -> list[tuple[str, str, int]]:
		for fromId in list(self._forwardBi.keys()):
			fromWord = self._unigrams[fromId].word
			for toId in self._forwardBi[fromId].counts:
				toWord = self._unigrams[toId].word
				yield (fromWord, toWord, self._forwardBi[fromId].counts[toId])
				
	

	