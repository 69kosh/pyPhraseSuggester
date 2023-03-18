from pyPhraseSuggesting.finder import Finder
from pyPhraseSuggesting.memoRepo import MemoRepo
import pandas as pd

unigrams = [('мама', 2), ('мыла', 3), ('раму', 2), ('руки', 1), ('мылом', 1), ('кусок', 1), ('_', 4)]
bigrams = [('_', 'мама', 1), ('мама', 'мыла', 1), ('мыла', 'раму', 1), ('мыла', 'руки', 1), ('руки', 'мылом', 1),
           ('раму', '_', 1), ('мылом', '_', 1), ('_', 'кусок', 1), ('кусок', 'мыла', 1), ('мыла', '_', 1)]


# unigrams = pd.read_csv("unigrams.csv", encoding='utf8', header=None).to_dict('split')['data']
# bigrams = pd.read_csv("bigrams.csv", encoding='utf8', header=None).to_dict('split')['data']

# unigrams = pd.read_csv("unigrams.cyr.lc", encoding='utf8', header=None, delimiter='\t').to_dict('split')['data']
# bi = pd.read_csv("bigrams.cyrB.lc", encoding='utf8', header=None, delimiter='\t')
# bi[2] = bi[1]
# bi[[0,1]] = bi[0].str.split(' ', 1 , expand= True)
# bigrams = bi.to_dict('split')['data']


# def test_phrase_split():
#     print(len(bigrams))
#     finder = Finder(MemoRepo(unigrams, bigrams))
#     print(finder.find('мыла'))
#     assert 0

