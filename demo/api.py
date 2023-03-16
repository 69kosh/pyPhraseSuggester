from pyPhraseSuggesting import Finder, MemoRepo
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

unigrams = pd.read_csv("unigrams.csv", encoding='utf8', header=None, delimiter=',').to_dict('split')['data']
bigrams = pd.read_csv("bigrams.csv", encoding='utf8', header=None, delimiter=',').to_dict('split')['data']

repo = MemoRepo(unigrams=unigrams, bigrams=bigrams)
finder = Finder(repo)

@app.get("/")
async def find(phrase: str ='', limit: int = 20):
    result = finder.find(phrase=phrase, limit = limit)
    return [' '.join(item.words) for item in result][0:limit]#.strip('_ ')
