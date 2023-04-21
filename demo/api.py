import sys
sys.path.append('../src')
import os
from pyPhraseSuggester import Finder, MemoRepo, Updater
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every

path = os.path.dirname(os.path.realpath(__file__))
repo:MemoRepo = None
finder:Finder = None
finder:Updater = None
phrases = []
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def find(phrase: str ='', limit: int = 20):
    result = finder.find(phrase=phrase, limit = min(max(limit, 100), 1000))
    return [' '.join(item.words) for item in result[0:limit]]

@app.post("/add")
async def add(phrase: str):
    global phrases
    phrases.append(phrase)

@app.on_event("startup")
def initFinder() -> None:
    global finder, updater, repo
    repo = MemoRepo()
    finder = Finder(repo)
    updater = Updater(repo)
    print('loading...')
    updater.loadUnigrams(path+'/unigrams.csv')
    updater.loadBigrams(path+'/bigrams.csv')
    print('loaded')

@app.on_event("startup")
@repeat_every(seconds=10, wait_first=True)
def addPhrases() -> None:
    global phrases, updater
    if len(phrases):
        print('adding phrases:', phrases)
        updater.addPhrases(phrases)
        phrases = []
        print('added')



@app.on_event("startup")
@repeat_every(seconds=10*60, wait_first=True)
def saveRepo() -> None:
    print('saving...')
    global updater
    updater.saveUnigrams(path+'/unigrams.csv')
    updater.saveBigrams(path+'/bigrams.csv')
    print('saved')

