

from random import random
from io import StringIO
import csv
import nltk.data
from nltk.tokenize import RegexpTokenizer
from nltk.util import ngrams as nGrams
from dataclasses import dataclass, field

@dataclass(slots=True)
class Gram:
    cnt: int = 0
    bi: dict[str, int] = field(default_factory={})

def loadAndSplit(instance) -> dict[str, Gram]:

    print(instance)

    tokenizer = nltk.data.load('tokenizers/punkt/russian.pickle')
    wordsTokenizer = RegexpTokenizer(r'[\w-]+')

    result: dict[str, Gram] = {}

    csvStr = ''
    with open(file=instance[0], mode='r', encoding='utf8') as file:
        # пропускаем до след строки. Есть проблема с csv - иногда csv-строки содержат \n внутри, и получаются битые
        # тройной трай для обхода проблем с utf8 дискретностью
        file.seek(instance[1])
        try:
            file.readline()
        except Exception as e:
            # print(e)
            file.seek(instance[1]+1)
            try:
                file.readline()
            except Exception as e:
                # print(2,e)
                file.seek(instance[1]+2)
                file.readline()

        # читаем строки
        while file.tell() <= instance[2]:
            pos = file.tell()
            line = file.readline()
            # print(pos, file.tell(), line)
            csvStr += line

    # парсим csv, извлекаем предлоения, из них слова
    csvFile = StringIO(csvStr)
    reader = csv.reader(csvFile, delimiter=',')
    allWords = ['_']
    for row in reader:
        for str in row:
            sentences = tokenizer.tokenize(str)
            for sentence in sentences:
                allWords.extend(wordsTokenizer.tokenize(sentence.lower()))
                # добавляем маркер конца
                allWords.append('_')
                # words.insert(0, '_')

    # весь словарь
    unigrams = list(set(allWords))
    # print('uni', len(unigrams))
    for ngram in unigrams:
        key1 = ngram
        if key1 not in result:
            result[key1] = Gram(0, {})

    # слова в биграммы
    bigrams = list(nGrams(allWords, 2))
    # print('bi', len(bigrams))
    for ngram in bigrams:
        key1 = ngram[0]
        key2 = ngram[1]
        # print(key)
        if key1 in result:
            if key2 in result[key1].bi:
                result[key1].cnt += 1
                result[key1].bi[key2] += 1
            else:
                result[key1].cnt += 1
                result[key1].bi[key2] = 1
        else:
            result[key1] = Gram(0, {})
            result[key1].cnt += 1
            result[key1].bi[key2] = 1

    # print('res', len(result))
    # return pickle.dumps(result)
    # print('pickle', res)
    return result
def combine(estimate_a: dict[str, Gram], estimate_b: dict[str, Gram]) -> dict[str, Gram]:
# def combine(estimate_a, estimate_b):
    l1 = len(estimate_a)
    l2 = len(estimate_b)
    # print(l1, l2)

    result = estimate_a
    for key1 in estimate_b:
        b = estimate_b[key1]
        if key1 in result:
            res = result[key1] 
            for key2 in b.bi:
                cnt = b.bi[key2]
                res.cnt += cnt
                if key2 in res.bi:
                    res.bi[key2] += cnt
                else:
                    res.bi[key2] = cnt

            result[key1] = res
        else:
            result[key1] = b

    # оптимизация: если больше 100т слов в результате, то это финальная сборка,
    # и её надо почистить от одиночных биграмм, где биграмм на слово больше 1т
    # if len(result) > 100000:
    #     for key1 in result:
    #         if len(result[key1]['bi']) > 1000:
    #             res = {}
    #             for key2 in result[key1]['bi']:
    #                 if result[key1]['bi'][key2] > 1:
    #                     res[key2] = result[key1]['bi'][key2]
    #             result[key1]['bi'] = res

    print(l1, l2, len(result))
    # return pickle.dumps(result)
    return result

if __name__ == '__main__':
    import time
    import mr4mp
    import os
    import multiprocessing
    import csv

    multiprocessing.Pool

    filename = "lenta-ru-news.csv"
    maxSplitSize = 1024*1024  # количество байт в одном куске на обработку
    cpuCount = multiprocessing.cpu_count()
    fileSize = os.path.getsize(filename)
    chunks = [(filename, offset*maxSplitSize, (offset + 1)*maxSplitSize)
              for offset in range(0, fileSize//maxSplitSize)]
    # print(chunks)
    chunksCount = len(chunks)
    # processes = min(chunksCount, cpuCount) # cpuCount#
    print(cpuCount, chunksCount, fileSize)
    start_time = time.time()
    result = mr4mp.pool(12).mapreduce(loadAndSplit, combine, chunks)
    print("--- %s seconds ---" % (time.time() - start_time))

    # result = pickle.loads(result)

    # формируем csv униграм
    with open('unigrams.csv', 'w', encoding='utf8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for key in result:
            writer.writerow([key, result[key].cnt])

    # формируем csv биграм
    with open('bigrams.csv', 'w', encoding='utf8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for key in result:
            for key2 in result[key].bi:
                # if result[key]['bi'][key2] > 1:
                writer.writerow([key, key2, result[key].bi[key2]])
