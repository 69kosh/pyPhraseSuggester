import sys
sys.path.append('src')

from pyPhraseSuggester import Finder, MemoRepo


import csv
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

with open(dir_path+'/grams/unigrams.cyr.lc', encoding='utf8') as csvfile:
    unigrams = [row for row in csv.reader(csvfile, delimiter='\t')]
with open(dir_path+'/grams/bigrams.cyrB.lc', encoding='utf8') as csvfile:
    bigrams = [row[0].split(' ') + [row[1]] for row in csv.reader(csvfile, delimiter='\t')]
print(bigrams[0:5])

# загружаем словари в репозиторий
repo = MemoRepo(unigrams=unigrams, bigrams=bigrams)

# инициируем файндер
finder = Finder(repo)

# запрашиваем вероятные цепочки слов по фразе
chains = finder.find('путин дво')

# выводим 5 лучших
print([' '.join(chain.words) for chain in chains[0:5]])
