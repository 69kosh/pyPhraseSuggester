from contextlib import ContextDecorator
from dataclasses import dataclass
from .abcRepo import ABCRepo

from functools import wraps
import time
import re


def timeit(func):
	@wraps(func)
	def timeit_wrapper(*args, **kwargs):
		start_time = time.perf_counter()
		result = func(*args, **kwargs)
		end_time = time.perf_counter()
		total_time = end_time - start_time
		print(
			f'Function {func.__name__} {kwargs} Took {total_time:.4f} seconds')
		return result
	return timeit_wrapper


@dataclass
class Chain:
	words: list[str]
	ids: list[int]
	prob: float


class Finder(ContextDecorator):
	def __init__(self, repo: ABCRepo) -> None:
		super().__init__()
		self.repo = repo

	def __enter__(self, repo: ABCRepo) -> None:
		self.repo = repo
		return self

	def __exit__(self, *exc):
		self.repo.close()

	def _splitPhrase(self, phrase: str):
		wordsTokenizer = re.compile(r'[\w-]+', re.UNICODE | re.MULTILINE | re.DOTALL)
		words = wordsTokenizer.findall(phrase.lower())
		# print(phrase.lower(), words, phrase[-1] == ' ')
		# print(words, words[0:-1])
		if len(phrase) < 1:
			return ([], '')
		if phrase[-1] == ' ':
			return (words, '')
		else:
			return (words[0:-1], words[-1])

	def _getBiForwardProb(self, id1, id2) -> float:
		bi = self.repo.getForwardBigrams(id1)
		if bi and id2 in bi.words:
			return bi.words[id2]
		else:
			return 0.0  # min(bi.words.values())

	def _calcChainProb(self, ids) -> float:
		p = 1.0
		if len(ids) < 2:
			return p
		idids = list(zip(ids[0:-1], ids[1:]))
		# print(idids)
		for idid in idids:
			p *= self._getBiForwardProb(idid[0], idid[1])

		return p

	def _intersectIdsForward(self, id, ids):
		bi = self.repo.getForwardBigrams(id)
		# print(bi)
		# for id in bi.words.keys():
		#     print(self.repo.getUnigrams([id]))
		if bi:
			return list(set(ids) & set(bi.words.keys()))
		else:
			return []

	def _appendToChain(self, chain: Chain, id: str | int, word: str) -> Chain:
		if len(chain.ids):
			return Chain(ids=chain.ids + [id], words=chain.words + [word], prob=chain.prob * self._getBiForwardProb(chain.ids[-1], id))
		else:
			return Chain(ids=[id], words=[word], prob=chain.prob)

	def _prependToChain(self, chain: Chain, id: str | int, word: str) -> Chain:
		if len(chain.ids):
			return Chain(ids=[id] + chain.ids, words=[word] + chain.words, prob=chain.prob * self._getBiForwardProb(id, chain.ids[0]))
		else:
			return Chain(ids=[id], words=[word], prob=chain.prob)

	def _sortAndLimitChains(self, chains: list[Chain], limit=100) -> list[Chain]:
		newChains = sorted(chains, key=lambda x: x.prob, reverse=True)
		return newChains[0:limit]

	def _getSEId(self):
		# конец-начало
		seUni = self.repo.findWords(['_'])
		# print(seUni)
		if seUni[0] is not None:
			startEndUni = seUni[0]
			seId = startEndUni.id
		else:
			seId = -1

		return seId

	@timeit
	def _permanentChains(self, phrase, limit: int = 100) -> list[Chain]:
		chains: list[Chain] = []
		newChains: list[Chain] = []

		(words, half) = self._splitPhrase(phrase)
		# print((words, half))

		seId = self._getSEId()

		# можем и не найти, надо обрабатывать
		permanentUnis = self.repo.findWords(words)
		if None in permanentUnis:
			chains.append(Chain([], [], 1.0))
			# если слова не обнаружены в словаре - берём самые близкие
			# комбинируем, получая множество цепочек
			for uni, word in zip(permanentUnis, words):
				if uni is None:
					probs = self.repo.matchFuzzyWords(word, 10)
					# print(probs)
					ids = list(probs.keys())
					unis = self.repo.getUnigrams(ids)

					if len(unis) == 0:
						return []  # вообще ничего не нашли
					
					newChains: list[Chain] = []
					# создаем новые цепочки на основе старого списка, 
					# размножая каждую цепочку на найденные варианты
					for chain in chains:
						for uni in unis:
							newChains.append(self._appendToChain(
								chain=chain, id=uni.id, word=uni.word))

					chains = newChains
				else:
					newChains: list[Chain] = []
					# если слово определено, то добавляем его во все цепочки не приумножая их
					for chain in chains:
						newChains.append(self._appendToChain(
							chain=chain, id=uni.id, word=uni.word))

					chains = newChains
		else:
			# однозначная цепочка
			chains.append(Chain([x.word for x in permanentUnis],
								[x.id for x in permanentUnis],
								self._calcChainProb([x.id for x in permanentUnis])
			))

		# если последнее слово закончено, возвращаем цепочки
		# print(chains)
		if half == '' and words:
			return chains

		# если пусто - ищем несколько самых популярных слов
		if half == '' and len(words) == 0:
			if seId >= 0:
				# есть стартовый токен - достаем вероятость по биграме
				bi=self.repo.getForwardBigrams(seId)
				sumCnt=sum(list(bi.words.values()))
				matchedProbs=dict([(key, bi.words[key] / sumCnt)
								for key in bi.words])
			else:
				# тупо самые популярные слова
				ids = self.repo.matchWords('', limit=limit)
				matchedProbs=dict([(id, 1.0) for id in ids])
		else:
			# иначе ищем подходящие неоконченные слова
			# в т.ч. берём в расчет все слова из биграм 
			ids = []
			for chain in chains:
				if len(chain.ids):
					bi=self.repo.getForwardBigrams(chain.ids[-1])
					if bi:
						ids += bi.words.keys()

			matchedProbs=self.repo.matchFuzzyWords(half, len(ids) + 10000, ids)

		matchedIds=list(matchedProbs.keys())

		# взвешиваем с учетом популярности слова
		unis = self.repo.getUnigrams(matchedIds)
		sumCnt=sum([uni.count for uni in unis])

		# выбираем максимальное значение либо по популярности слова, 
		# либо по совпадению, а если слово начинается с указанного, 
		# то еще + 0.5

		matchedProbs=dict([(uni.id, (
				0.5 * (uni.word.find(half, 0) == 0) + 
				0.5 * max((uni.count / sumCnt), matchedProbs[uni.id])
			)) for uni in unis])



		newChains: list[Chain] = []
		# для каждой цепочки
		for chain in chains:
			#  если она не пустая, то фильтруем список подходящих слов по вероятности быть в биграме
			if len(chain.ids):
				ids = self._intersectIdsForward(chain.ids[-1], matchedIds)
			else:
				ids = matchedIds

			# для каждого оставшегося варианта порождаем еще одну цепочку с ним
			for id in ids:
				prob = chain.prob * matchedProbs[id]
				if prob > 0 and id not in chain.ids and id != seId:
					uni=self.repo.getUnigrams([id])[0]
					newChains.append(Chain(
						chain.words + [uni.word],
						chain.ids + [uni.id],
						prob))

		chains=self._sortAndLimitChains(newChains, limit)
		return chains

	@ timeit
	def _expandChainsForward(self, chains: list[Chain], inception: int=2, limit: int=100, threshold=0.0001):

		seId=self._getSEId()
		# ищем вперёд подхощяние для продолжения фраз слова
		processedChains=[]
		added=len(chains)
		level=0
		while added > 0 and level < inception:
			level += 1
			# print(inception, len(chains))
			lastLen=len(chains)
			for chain in chains.copy():
				# пропускаем если конец фразы уже найден
				if chain.ids[-1] == seId or chain in processedChains:
					continue
				# print(chain.ids[-1], minProb)
				bi=self.repo.getForwardBigrams(chain.ids[-1])

				# надо отбросить все биграмы, которые буду ниже минимальной вероятности последнего элемента в ограниченном списке
				minProb=min(chains, key=lambda x: x.prob).prob if len(
					chains) >= limit else threshold
				ids=[]
				if bi is not None:
					for id, prob in bi.words.items():
						if prob*chain.prob < minProb:
							continue
						# print(id)
						if id != seId and id in chain.ids:
							continue

						ids.append(id)
				# print(bi, ids)
				unis=self.repo.getUnigrams(ids)
				# print(len(unis))
				for uni in unis:

					newChain=self._appendToChain(
						chain=chain, id=uni.id, word=uni.word)
					if newChain in chains or (len(chains) > limit and newChain.prob < minProb):
						continue

					# print(newChain)
					chains.append(newChain)
					minProb=min(minProb, newChain.prob)

				processedChains.append(chain)

				chains=self._sortAndLimitChains(chains, limit)

			added=len(chains) - lastLen

		return chains

	@ timeit
	def _expandChainsBackward(self, chains: list[Chain], inception: int=2, limit: int=100, threshold=0.0001):

		seId=self._getSEId()
		# ищем назад подхощяние для продолжения фраз слова
		processedChains=[]
		added=len(chains)
		level=0
		while added > 0 and level < inception:
			level += 1
			lastLen=len(chains)
			minProb=min(
				chains, key=lambda x: x.prob).prob if lastLen >= limit else threshold
			# print(level, len(chains), minProb)
			for chain in chains.copy():
				# пропускаем если конец фразы уже найден
				if chain.ids[0] == seId or chain in processedChains:
					continue

				bi=self.repo.getBackwardBigrams(chain.ids[0])
				ids=[]
				if bi is not None:
					for id, prob in bi.words.items():
						# print('skip', id, prob*chain.prob , minProb)
						if prob*chain.prob < minProb:
							continue

						if id != seId and id in chain.ids:
							continue

						ids.append(id)
				unis=self.repo.getUnigrams(ids)
				# print(unis)
				for uni in unis:
					newChain=self._prependToChain(chain=chain,
													id=uni.id,
													word=uni.word)
					if newChain in chains or (lastLen >= limit and newChain.prob < minProb):
						# print('skip', chain.prob, newChain.prob , minProb)
						continue

					chains.append(newChain)
					minProb=min(minProb, newChain.prob)

				processedChains.append(chain)

				chains=self._sortAndLimitChains(chains)

			added=len(chains) - lastLen

		return chains

	def find(self, phrase: str, limit=100) -> list[Chain]:

		chains: list[Chain]=self._permanentChains(phrase, limit=limit*10)
		chains=self._expandChainsForward(
			chains, inception=2, limit=limit*5, threshold=0.0001)
		chains=self._expandChainsBackward(
			chains, inception=2, limit=limit*5, threshold=0.0001)

		return chains
