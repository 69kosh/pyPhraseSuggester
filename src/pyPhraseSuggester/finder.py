from contextlib import ContextDecorator
from dataclasses import dataclass
from .abcRepo import ABCRepo, Unigram, Bigrams

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
    bias: float

    def __hash__(self):
        return hash(' '.join(self.words))


class Finder:#(ContextDecorator):
    def __init__(self, repo: ABCRepo) -> None:
        # super().__init__()
        self.repo = repo

    # def __enter__(self, repo: ABCRepo) -> None:
    #     self.repo = repo
    #     return self

    # def __exit__(self, *exc):
    #     self.repo.close()

    def splitPhrase(self, phrase: str) -> tuple[list[str], str]:
        wordsTokenizer = re.compile(
            r'[\w-]+', re.UNICODE | re.MULTILINE | re.DOTALL)
        words = wordsTokenizer.findall(phrase.lower())
        if len(phrase) < 1:
            return ([], '')
        if phrase[-1] == ' ':
            return (words, '')
        else:
            return (words[0:-1], words[-1])

    def calcMinProb(self, chains: list[Chain], lowTheshold=0.01, softLimit=100) -> float:
        if len(chains):
            if len(chains) > softLimit:
                sortedChains = sorted(
                    chains, key=lambda x: x.prob, reverse=True)
                minProb = sortedChains[softLimit - 1].prob
            else:
                minProb = lowTheshold * max(chains, key=lambda x: x.prob).prob
        else:
            minProb = 0.0

        return minProb

    def combineWordsToChains(self, chains: list[Chain], unigrams: list[Unigram], probs: dict[float], lowTheshold=0.01, softLimit=100) -> list[Chain]:
        ''' Добавляем новое слово/слова к цепочкам, порождая новые
                В каждую цепочку пытаемся вставить каждое слово в каждую позицию,
                откидываем вариванты ниже порога. Так же пропускаем вариант без вставки
                Порог считаем, либо как часть от максимальной (Pmax *0.01), если мы входим в софтлимит 
                по количеству вариантов, либо, если стало больше софтлимит как P последнего элемента лимита 
                (пока нет, пока только минимальный, его проще получить - без сортировки)
        '''
        resChains: dict[Chain] = {}

        wordsBigrams = dict(
            [(uni.id, self.repo.getForwardBigrams(uni.id)) for uni in unigrams])

        for chain in chains:

            # тупо в лоб достаем все биграммы для расчета вероятности
            # пробегаемся по позициям, подставляя слова, добавляя годные варианты
            chainBigrams = dict(
                [(id, self.repo.getForwardBigrams(id)) for id in chain.ids])

            bigrams = chainBigrams | wordsBigrams

            minProb = self.calcMinProb(
                list(resChains.values()), lowTheshold=lowTheshold, softLimit=softLimit)

            for place in range(0, len(chain.ids) + 1):
                for uni in unigrams:
                    id = uni.id
                    word = uni.word
                    wordBi = wordsBigrams[id]

                    if wordBi is None and place < len(chain.ids):
                        continue

                    bias = chain.bias * probs[id]  # база старая и база новая
                    p = bias
                    ids = chain.ids[:]
                    ids.insert(place, id)
                    words = chain.words[:]
                    words.insert(place, word)
                    if len(ids) < 2:
                        ch = Chain(words, ids, p, bias)
                        resChains[hash(ch)] = ch
                        continue

                    idids = list(zip(ids[0:-1], ids[1:]))

                    stop = False
                    for (id1, id2) in idids:
                        if id1 in bigrams:
                            if bigrams[id1] is not None and id2 in bigrams[id1].words:
                                p *= bigrams[id1].words[id2]
                            else:
                                stop = True
                                break

                        if p < minProb:
                            # print(minProb)
                            stop = True
                            break

                    if not stop:
                        ch = Chain(words, ids, p, bias)
                        resChains[hash(ch)] = ch
                        # resChains.add(Chain(words, ids, p, bias))

        return list(resChains.values())


    @ timeit
    def getChainsByWords(self, words: list[str], lowTheshold=0.01, softLimit=100, fuzzyLimit=500, limit=100) -> list[Chain]:
        ''' Из списка слов формируем возможны варианты цепочек
                Если все слова найдены, то варианты есть только у последнего слова, используемого как префикс
                Если есть нераспозананные слова, то цепочки размножаются из найденных вариантов нечеткого поиска, 
                последнее слово тоже по префиксу
                Для каждого из кандидатов считаем вероятность, и откидываем, если она слишком низкая
                Порог считаем, либо как часть от максимальной (Pmax *0.01), если мы входим в софтлимит 
                по количеству вариантов, либо, если стало больше софтлимит как P последнего элемента лимита
        '''
        chains: list[Chain] = [Chain([], [], 1.0, 1.0)]
        # if len(words) == 0:
        unis = self.repo.findWords(words)
        for word in words:
            if word == '':
                # если еще ничего не ввели, берём биграммы последних слов цепочек, и используем их
                # если вообще нет слов, берём просто популярные слова
                ids = []
                for chain in chains:
                    if len(chain.ids):
                        bi = self.repo.getForwardBigrams(chain.ids[-1])
                        if bi is not None:
                            ids += list(bi.words.keys())[0:fuzzyLimit]

                if len(ids) < fuzzyLimit:
                    ids += self.repo.matchWords('', fuzzyLimit)
                
                fuzzyProbs = dict(zip(ids, [1.0]*len(ids)))

            else:
                fuzzyProbs = self.repo.matchFuzzyWords(word, fuzzyLimit)


            fuzzyIds = list(fuzzyProbs.keys())
            fuzzyUnis = self.repo.getUnigrams(fuzzyIds)

            # взвешиваем с учетом популярности слова
            sumCnt = sum([uni.count for uni in fuzzyUnis])
            maxCnt = max([uni.count for uni in fuzzyUnis] + [0])

            # выбираем максимальное значение либо по популярности слова,
            # либо по совпадению, а если слово начинается с указанного,
            # то еще + 0.25

            matchedProbs = dict([(uni.id, (
                0.1 * (uni.word.find(word, 0) == 0) +
                0.1 * (uni.count / maxCnt) +
                0.1 * fuzzyProbs[uni.id] * fuzzyProbs[uni.id]
            ) if (uni.word != word) else 1.0) for uni in fuzzyUnis])

            chains = self.combineWordsToChains(
                    chains, fuzzyUnis, matchedProbs, lowTheshold, softLimit)

        chains = self.sortAndLimitChains(chains, limit)
        return chains

    def _getBiForwardProb(self, id1, id2) -> float:
        bi = self.repo.getForwardBigrams(id1)
        if bi and id2 in bi.words:
            return bi.words[id2]
        else:
            return 0.0

    def _appendToChain(self, chain: Chain, id: str | int, word: str) -> Chain:
        if len(chain.ids):
            return Chain(ids=chain.ids + [id], words=chain.words + [word], prob=chain.prob * self._getBiForwardProb(chain.ids[-1], id), bias=chain.bias)
        else:
            return Chain(ids=[id], words=[word], prob=chain.prob, bias=chain.bias)

    def _prependToChain(self, chain: Chain, id: str | int, word: str) -> Chain:
        if len(chain.ids):
            return Chain(ids=[id] + chain.ids, words=[word] + chain.words, prob=chain.prob * self._getBiForwardProb(id, chain.ids[0]), bias=chain.bias)
        else:
            return Chain(ids=[id], words=[word], prob=chain.prob, bias=chain.bias)

    def sortAndLimitChains(self, chains: list[Chain], limit=100) -> list[Chain]:
        return sorted(chains, key=lambda x: x.prob, reverse=True)[0:limit]

    @ timeit
    def expandChainsForward(self, chains: list[Chain], inception: int = 2, limit: int = 100, lowTheshold=0.01):

        chains = dict([(hash(chain), chain) for chain in chains])

        # ищем вперёд подхощяние для продолжения фраз слова
        processedChains = []
        added = len(chains)
        level = 0
        while added > 0 and level < inception:
            level += 1
            # print(inception, len(chains))
            lastLen = len(chains)
            for chain in list(chains.values()):
                # пропускаем если цепочку уже обработали
                if chain in processedChains:  
                    continue

                bi = self.repo.getForwardBigrams(chain.ids[-1])

                minProb = self.calcMinProb(
                    list(chains.values()), lowTheshold=lowTheshold, softLimit=limit)

                ids = []
                if bi is not None:
                    for id, prob in bi.words.items():
                        if prob*chain.prob < minProb:
                            continue
                        ids.append(id)

                unis = self.repo.getUnigrams(ids)

                for uni in unis:

                    newChain = self._appendToChain(
                        chain=chain, id=uni.id, word=uni.word)
                    if newChain in chains or (len(chains) > limit and newChain.prob < minProb):
                        continue

                    # print(newChain)
                    chains[hash(newChain)] = newChain
                    minProb = min(minProb, newChain.prob)

                processedChains.append(chain)

                chains = self.sortAndLimitChains(list(chains.values()), limit)
                chains = dict([(hash(chain), chain) for chain in chains])

            added = len(chains) - lastLen

        return list(chains.values())

    @ timeit
    def expandChainsBackward(self, chains: list[Chain], inception: int = 2, limit: int = 100, lowTheshold=0.01):

        chains = dict([(hash(chain), chain) for chain in chains])

        # ищем назад подхощяние для продолжения фраз слова
        processedChains = []
        added = len(chains)
        level = 0
        while added > 0 and level < inception:
            level += 1
            lastLen = len(chains)

            minProb = self.calcMinProb(
                    list(chains.values()), lowTheshold=lowTheshold, softLimit=limit)

            for chain in list(chains.values()):
                # пропускаем если цепочку уже обработали
                if chain in processedChains: 
                    continue

                bi = self.repo.getBackwardBigrams(chain.ids[0])
                ids = []
                if bi is not None:
                    for id, prob in bi.words.items():
                        # print('skip', id, prob*chain.prob , minProb)
                        if prob*chain.prob < minProb:
                            continue
                        ids.append(id)

                unis = self.repo.getUnigrams(ids)
                # print(unis)
                for uni in unis:
                    newChain = self._prependToChain(chain=chain,
                                                    id=uni.id,
                                                    word=uni.word)
                    if newChain in chains or (lastLen >= limit and newChain.prob < minProb):
                        # print('skip', chain.prob, newChain.prob , minProb)
                        continue

                    chains[hash(newChain)] = newChain
                    minProb = min(minProb, newChain.prob)

                processedChains.append(chain)

                chains = self.sortAndLimitChains(list(chains.values()), limit)
                chains = dict([(hash(chain), chain) for chain in chains])

            added = len(chains) - lastLen

        return list(chains.values())

    def find(self, phrase: str, limit=100) -> list[Chain]:

        (words, half) = self.splitPhrase(phrase)

        chains = self.getChainsByWords(words=words + [half])
        chains = self.expandChainsForward(chains, limit=limit)
        chains = self.expandChainsBackward(chains, limit=limit)

        return chains
