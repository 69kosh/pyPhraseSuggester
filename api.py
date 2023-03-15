import sys
sys.path.append('src/')

from pyPhraseSuggesting import Finder, MemoRepo
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

# unigrams = [('мама', 2), ('мыла', 3), ('раму', 2), ('руки', 1), ('мылом', 1), ('кусок', 1), ('_', 4)]
# bigrams = [('_', 'мама', 1), ('мама', 'мыла', 1), ('мыла', 'раму', 1), ('мыла', 'руки', 1), ('руки', 'мылом', 1),
#            ('раму', '_', 1), ('мылом', '_', 1), ('_', 'кусок', 1), ('кусок', 'мыла', 1), ('мыла', '_', 1)]

unigrams = pd.read_csv("grams/unigrams.csv", encoding='utf8', header=None).to_dict('split')['data']
bigrams = pd.read_csv("grams/bigrams.csv", encoding='utf8', header=None).to_dict('split')['data']

# unigrams = pd.read_csv("grams/unigrams.cyr.lc", encoding='utf8', header=None, delimiter='\t').to_dict('split')['data']
# bi = pd.read_csv("grams/bigrams.cyrB.lc", encoding='utf8', header=None, delimiter='\t')
# bi[2] = bi[1]
# bi[[0,1]] = bi[0].str.split(' ', 1 , expand= True)
# bigrams = bi.to_dict('split')['data']

repo = MemoRepo(unigrams=unigrams, bigrams=bigrams)
finder = Finder(repo)

@app.get("/")
async def find(phrase: str ='', limit: int = 20):
    result = finder.find(phrase=phrase)[0:limit]
    return [' '.join(item.words) for item in result]# if item.prob > 0.05]
