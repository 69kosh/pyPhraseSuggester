import pytest
from pyPhraseSuggester.memoRepo import *

@pytest.fixture
def repo():
    unigrams = [('мама', 2), ('мыла', 3), ('раму', 2), ('руки', 1), ('мылом', 1), ('кусок', 1), ('_', 4)]
    bigrams = [('_', 'мама', 1), ('мама', 'мыла', 1), ('мыла', 'раму', 1), ('мыла', 'руки', 1), ('руки', 'мылом', 1),
           ('раму', '_', 1), ('мылом', '_', 1), ('_', 'кусок', 1), ('кусок', 'мыла', 1), ('мыла', '_', 1)]
    repo = MemoRepo()
    repo.addUnigrams(unigrams)
    repo.addBigrams(bigrams)
    return repo


def test_getUnigrams(repo:ABCRepo):
    uni1 = repo.getUnigrams([1])
    assert len(uni1) == 1

    unis = repo.getUnigrams([0, 100500, 1, 2], limit=3)

    assert len(unis) == 3
    assert unis[1] == None
    assert unis[2].word == uni1[0].word

def test_findWords(repo:ABCRepo):
    unis = repo.getUnigramsByWords(['мама', 'мыла', 'ноги', 'мылом'])

    assert len(unis) == 4
    assert unis[1].word == 'мыла'
    assert unis[2] == None


def test_matchPrefix(repo:ABCRepo):
    unis = repo.getUnigramsByWords(['мыла', 'мама', 'мылом', '_', 'мыла'])

    ids = repo.matchPrefix('м', limit = 2)
    assert ids == [unis[0].id, unis[1].id]

    ids = repo.matchPrefix('х', limit = 2)
    assert ids == []

    ids = repo.matchPrefix('мы', limit = 2)
    assert ids == [unis[0].id, unis[2].id]

    ids = repo.matchPrefix('хм', limit = 2)
    assert ids == []

    ids = repo.matchPrefix('мыл', limit = 2) 
    assert ids == [unis[0].id, unis[2].id]

    ids = repo.matchPrefix('мыло', limit = 2) 
    assert ids == [unis[2].id]

    ids = repo.matchPrefix('абырвалг', limit = 2) 
    assert ids == []

    ids = repo.matchPrefix('', limit = 2) 
    assert ids == [unis[3].id, unis[4].id]


def test_matchFuzzy(repo:ABCRepo):
    unis = repo.getUnigramsByWords(['мыла', 'мылом'])
    probs = repo.matchFuzzy('мылом')
    assert list(probs.keys()) == [unis[1].id, unis[0].id]

    probs = repo.matchFuzzy('foo')
    assert probs == {}

def test_getForwardBigrams(repo:ABCRepo):
    unis = repo.getUnigramsByWords(['мыла', 'раму', 'руки', '_'])
    bi = repo.getForwardBigrams(unis[0].id)
    assert bi is not None
    assert unis[0].id not in bi.words
    assert unis[1].id in bi.words
    assert unis[2].id in bi.words
    assert unis[3].id in bi.words
    bi = repo.getForwardBigrams(100500)
    assert bi is None


def test_getBackwardBigrams(repo:ABCRepo):
    unis = repo.getUnigramsByWords(['мыла', 'мама', 'кусок'])
    bi = repo.getBackwardBigrams(unis[0].id)
    assert bi is not None
    assert unis[0].id not in bi.words
    assert unis[1].id in bi.words
    assert unis[2].id in bi.words
    bi = repo.getBackwardBigrams(100500)
    assert bi is None


def test_addUnigrams(repo:ABCRepo):
    unis = repo.getUnigramsByWords(['мыла', 'мама', 'мылом', '_', 'мыла'])
    ids = repo.matchPrefix('м', limit = 2)
    assert ids == [unis[0].id, unis[1].id]

    repo.addUnigrams([('мыла', 5), ('мылом', 10)])

    ids = repo.matchPrefix('м', limit = 2)
    assert ids == [unis[2].id, unis[4].id]


def test_addBigrams(repo:ABCRepo):
    repo.addUnigrams([('ноги', 1)])
    repo.addBigrams([('мыла', 'ноги', 1)])

    unis = repo.getUnigramsByWords(['мыла', 'раму', 'руки', 'ноги'])
    bi = repo.getForwardBigrams(unis[0].id)

    assert bi is not None
    assert unis[0].id not in bi.words
    assert unis[1].id in bi.words
    assert unis[2].id in bi.words
    assert unis[3].id in bi.words
