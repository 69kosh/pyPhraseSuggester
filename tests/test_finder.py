from pyPhraseSuggesting.finder import Finder
from pyPhraseSuggesting.memoRepo import MemoRepo
import pytest


@pytest.fixture
def repo():
    unigrams = [('мама', 2), ('мыла', 3), ('раму', 2),
                ('руки', 1), ('мылом', 1), ('кусок', 1)]
    bigrams = [('мама', 'мыла', 1), ('мыла', 'раму', 1), ('мыла', 'руки', 1), ('руки', 'мылом', 1),
               ('кусок', 'мыла', 1)]
    return MemoRepo(unigrams, bigrams)


@pytest.fixture
def finder(repo):
    return Finder(repo)


def getWords(chains):
    return [chain.words for chain in chains]


def test_splitPhrase(finder: Finder):

    (words, half) = finder.splitPhrase('')
    assert (words, half) == ([], '')

    (words, half) = finder.splitPhrase('мама')
    assert (words, half) == ([], 'мама')

    (words, half) = finder.splitPhrase('мама ')
    assert (words, half) == (['мама'], '')

    (words, half) = finder.splitPhrase('мама мыла')
    assert (words, half) == (['мама'], 'мыла')

    (words, half) = finder.splitPhrase('мама мыла ')
    assert (words, half) == (['мама', 'мыла'], '')


def test_getChainsByWords(finder: Finder):

    from pprint import pprint
    chains = finder.getChainsByWords([''])
    assert getWords(chains)[0:3] == [['мыла'], ['мама'], ['раму']]

    chains = finder.getChainsByWords(['м'])
    assert getWords(chains)[0:3] == [['мыла'], ['мама'], ['мылом']]

    chains = finder.getChainsByWords(['ма'])
    assert getWords(chains)[0:3] == [['мама']]

    chains = finder.getChainsByWords(['мама'])
    assert getWords(chains)[0:3] == [['мама']]

    chains = finder.getChainsByWords(['мама', ''])
    assert getWords(chains)[0:3] == [['мама', 'мыла']]

    chains = finder.getChainsByWords(['мыла', ''])
    assert getWords(chains)[0:3] == [['мама', 'мыла'], [
        'кусок', 'мыла'], ['мыла', 'раму']]

    chains = finder.getChainsByWords(['мыла', 'р'])
    assert getWords(chains)[0:3] == [['мыла', 'раму'], [
        'мыла', 'руки'], ['руки', 'мылом']]

    chains = finder.getChainsByWords(['м', ''], softLimit=100)
    assert len(chains) == 5

    chains = finder.getChainsByWords(['м', ''], softLimit=1)
    assert len(chains) == 4


def test_expandChainsForward(finder: Finder):

    baseChains = finder.getChainsByWords(['мама'])

    chains = finder.expandChainsForward(baseChains, inception=1)
    assert getWords(chains)[0:3] == [['мама'], ['мама', 'мыла']]

    chains = finder.expandChainsForward(baseChains, inception=3)
    assert getWords(chains)[0:5] == [['мама'], ['мама', 'мыла'], ['мама', 'мыла', 'раму'], [
        'мама', 'мыла', 'руки'], ['мама', 'мыла', 'руки', 'мылом']]

    chains = finder.expandChainsForward([])
    assert getWords(chains)[0:3] == []


def test_expandChainsBackward(finder: Finder):

    baseChains = finder.getChainsByWords(['раму'])

    chains = finder.expandChainsBackward(baseChains, inception=1)
    assert getWords(chains)[0:3] == [['раму'], ['мыла', 'раму']]

    chains = finder.expandChainsBackward(baseChains, inception=3)
    assert getWords(chains)[0:5] == [['раму'], ['мыла', 'раму'], ['мама', 'мыла', 'раму'], [
        'кусок', 'мыла', 'раму']]

    chains = finder.expandChainsBackward([])
    assert getWords(chains)[0:3] == []


def test_find(finder: Finder):
    from pprint import pprint
    chains = finder.find('мыла')
    words = getWords(chains)

    assert words == [['мыла'],
                    ['мама', 'мыла'],
                    ['кусок', 'мыла'],
                    ['мыла', 'раму'],
                    ['мыла', 'руки'],
                    ['мама', 'мыла', 'раму'],
                    ['кусок', 'мыла', 'раму'],
                    ['мама', 'мыла', 'руки'],
                    ['кусок', 'мыла', 'руки'],
                    ['мама', 'мыла', 'руки', 'мылом'],
                    ['кусок', 'мыла', 'руки', 'мылом'],
                    ['мылом'],
                    ['руки', 'мылом'],
                    ['мыла', 'руки', 'мылом']]

    chains = finder.find('')
    words = getWords(chains)

    assert words == [['мыла'],
                     ['мама', 'мыла'],
                     ['кусок', 'мыла'],
                     ['мама'],
                     ['раму'],
                     ['руки'],
                     ['мылом'],
                     ['кусок'],
                     ['руки', 'мылом'],
                     ['мама', 'мыла', 'раму'],
                     ['кусок', 'мыла', 'раму'],
                     ['мыла', 'раму'],
                     ['мама', 'мыла', 'руки'],
                     ['кусок', 'мыла', 'руки'],
                     ['мама', 'мыла', 'руки', 'мылом'],
                     ['кусок', 'мыла', 'руки', 'мылом'],
                     ['мыла', 'руки', 'мылом'],
                     ['мыла', 'руки']]
