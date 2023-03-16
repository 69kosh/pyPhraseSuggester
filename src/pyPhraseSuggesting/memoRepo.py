from .abcRepo import *
from rapidfuzz import *

class MemoRepo(ABCRepo):
	def __init__(self, unigrams, bigrams) -> None:
		super().__init__()

		self._prepareUnigrams(unigrams)
		self._prepareBigrams(bigrams, 10000)
		self._prepareFuzzyIndex()

		# print(sys.getsizeof(self._unigrams), len(self._unigrams))

	def _prepareUnigrams(self, unigrams):
		self._unigrams = []
		self._word2Id = {}
		self._prefix32Id = {}
		self._prefix22Id = {}
		self._prefix12Id = {}

		unigrams = sorted(unigrams, key=lambda x: x[1], reverse=True)

		id:int = 0
		for uni in unigrams:
			word = str(uni[0])
			cnt = int(uni[1])
			self._unigrams.append(Unigram(id, word, cnt))
			self._word2Id[word] = id

			if word[0] not in self._prefix12Id:
				self._prefix12Id[word[0:1]] = []
			self._prefix12Id[word[0:1]].append(id)

			if len(word) > 1:
				if word[0:2] not in self._prefix22Id:
					self._prefix22Id[word[0:2]] = []
				self._prefix22Id[word[0:2]].append(id)

			if len(word) > 2:
				if word[0:3] not in self._prefix32Id:
					self._prefix32Id[word[0:3]] = []
				self._prefix32Id[word[0:3]].append(id)

			id += 1
		
		# print(self._prefix12Id['f'])

	def _prepareBigrams(self, bigrams, limit = 100):
		self._forwardBi = {}
		self._backwardBi = {}

		for bi in bigrams:
			fromId = self._word2Id[str(bi[0])]
			toId = self._word2Id[str(bi[1])]
			count = int(bi[2])

			if fromId not in self._forwardBi:
				self._forwardBi[fromId] = Bigrams(
					id=fromId, count=count, words={toId: count})
			else:
				self._forwardBi[fromId].count += count
				if len(self._forwardBi[fromId].words) < limit:
					self._forwardBi[fromId].words[toId] = count

			if toId not in self._backwardBi:
				self._backwardBi[toId] = Bigrams(
					id=toId, count=count, words={fromId: count})
			else:
				self._backwardBi[toId].count += count
				if len(self._backwardBi[toId].words) < limit:
					self._backwardBi[toId].words[fromId] = count

		for id in self._forwardBi:
			for id2 in self._forwardBi[id].words:
				self._forwardBi[id].words[id2] /= self._forwardBi[id].count

		for id in self._backwardBi:
			for id2 in self._backwardBi[id].words:
				self._backwardBi[id].words[id2] /= self._forwardBi[id2].count

	def _prepareFuzzyIndex(self):
		self._fuzzyIndex = {}
		# для каждой униграмы разбиваем её на триграмы (может хватит би?)
		# и добавляем в словарь по ключу=триграмме ид униграмы
		# чтобы потом разбив слово на триграмы найти списки униграмы содержащих хотя бы одну из них
		# таким образом будем отсекать остальные слова из нечеткого поиска	
		for uni in self._unigrams:
			if len(uni.word) < 3:
				continue
			for i in range(0, len(uni.word)-2, 1):
				tri = uni.word[i:i+3]
				if tri not in self._fuzzyIndex:
					self._fuzzyIndex[tri] = []
				self._fuzzyIndex[tri].append(uni.id)

		# maxLen = 0
		# maxTri = ''
		# for tri in self._fuzzyIndex:
		# 	if maxLen < len(self._fuzzyIndex[tri]):
		# 		maxLen = len(self._fuzzyIndex[tri])
		# 		maxTri = tri
		# 		print(maxTri, maxLen)
		# print(self._fuzzyIndex, len(self._fuzzyIndex))

	def getUnigrams(self, ids: list[str | int], limit: int = 100) -> list[Unigram | None]:
		res = []
		for id in ids:
			res.append(self._unigrams[id])
		return res

	def findWords(self, words: list[str]) -> list[Unigram | None]:
		res = []
		for word in words:
			if word in self._word2Id:
				res.append(self._unigrams[self._word2Id[word]])
			else:
				res.append(None)
		return res

	def matchWords(self, prefix: str, limit: int = 100) -> list[str|int]:
		ids = []
		if len(prefix) > 2:
			if prefix[0:3] not in self._prefix32Id:
				return []
			if len(prefix) == 3:
				ids = self._prefix32Id[prefix[0:3]]
			else:
				for id in self._prefix32Id[prefix[0:3]]:
					uni = self._unigrams[id]
					if uni.word.find(prefix) == 0:
						ids.append(id)
		elif len(prefix) == 2:
			if prefix not in self._prefix22Id:
				return []
			ids = self._prefix22Id[prefix]
		elif len(prefix) == 1:
			if prefix not in self._prefix12Id:
				return []
			ids = self._prefix12Id[prefix]
		else:
			for uni in self._unigrams[0:limit]:
				ids.append(uni.id)

		# print(self._prefix32Id, prefix[0:3], len(prefix), ids)
		return ids

	def getForwardBigrams(self, id: str | int) -> Bigrams:
		if id in self._forwardBi:
			return self._forwardBi[id]


	def getBackwardBigrams(self, id: str | int) -> Bigrams:
		if id in self._backwardBi:
			return self._backwardBi[id]

	def matchFuzzyWords(self, word: str, limit: int = 100, additionalIds: list[str|int] = []) -> dict[str|int, float]:
		'''Для слов которые не нашли четко, подбираем близкие варианты
			Для этого используем сравнение по левенштейну, 
			а чтобы не перебирать все слова, бьем слово на триграмы и ищем 
			подходящие слова, с включением хотя бы 50% этих грам по индексу триграм
				https://pypi.org/project/rapidfuzz/'''
		...

		# если фраза короткая - ищем по префиксу
		# ids = []
		# if len(word) < 5:
		ids = self.matchWords(prefix=word, limit = limit) + additionalIds
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


		l = (len(word)-2) // 2 # половина токинов
		for id in counts:
			if counts[id] >= l:
				ids.append(id)
		
		# print(ids)
		unis = self.getUnigrams(set(ids))
		ratios = {}
		for uni in unis:
			ratios[uni.id] = (fuzz.ratio(word, uni.word) + 10.0)/110.0
			# print(word, uni.word, ratios[uni.id])
		
		
		ratios = dict(sorted(ratios.items(), key=lambda item: item[1], reverse=True))

		# print(dict(list(ratios.items())[0:limit]))
		return dict(list(ratios.items())[0:limit])

