from pyPhraseSuggesting import Finder, MemoRepo
from fastapi import FastAPI
import csv


with open('unigrams.csv', encoding='utf8') as csvfile:
    unigrams = [row for row in csv.reader(csvfile, delimiter=',')]
with open('bigrams.csv', encoding='utf8') as csvfile:
    bigrams = [row for row in csv.reader(csvfile, delimiter=',')]
    # bigrams = [row[0].split(' ')+[row[1]] for row in csv.reader(csvfile, delimiter='\t')]

repo = MemoRepo(unigrams=unigrams, bigrams=bigrams)
finder = Finder(repo)

app = FastAPI()

@app.get("/")
async def find(phrase: str ='', limit: int = 20):
    result = finder.find(phrase=phrase, limit = limit)
    return [' '.join(item.words) for item in result][0:limit]#.strip('_ ')
