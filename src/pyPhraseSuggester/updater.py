from .abcRepo import ABCRepo
import csv
import re

class Updater:
	def __init__(self, repo: ABCRepo) -> None:
		self.repo = repo

	def loadUnigrams(self, csvFilename = 'unigrams.csv'):
		with open(csvFilename, encoding='utf8') as csvfile:
			unigrams = [row for row in csv.reader(csvfile, delimiter=',')]
			self.repo.addUnigrams(unigrams)
	
	def loadBigrams(self, csvFilename = 'bigrams.csv'):
		with open(csvFilename, encoding='utf8') as csvfile:
			bigrams = [row for row in csv.reader(csvfile, delimiter=',')]
			self.repo.addBigrams(bigrams)

	def saveUnigrams(self, csvFilename = 'unigrams.csv'):
		with open(csvFilename, 'w', newline='', encoding='utf8') as csvfile:
			writer = csv.writer(csvfile, delimiter=',',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for row in self.repo.getAllUnigrams():
				writer.writerow(row)
	
	def saveBigrams(self, csvFilename = 'bigrams.csv'):
		with open(csvFilename, 'w', newline='', encoding='utf8') as csvfile:
			writer = csv.writer(csvfile, delimiter=',',
									quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for row in self.repo.getAllBigrams():
				writer.writerow(row)

	def splitProcessPhrases(self, phrases: list[str]) -> tuple[list[tuple[str, int]], list[tuple[str, str, int]]]:

		wordsTokenizer = re.compile(
			r'[\w-]+', re.UNICODE | re.MULTILINE | re.DOTALL)

		unigrams = {}
		bigrams = {}

		for phrase in phrases:
			words = wordsTokenizer.findall(phrase.lower())
			for word in words:
				if word in unigrams:
					unigrams[word][1] += 1
				else:
					unigrams[word] = [word, 1]

			if len(words) > 1:
				for (fromWord, toWord) in zip(words[:-1], words[1:]):
					key = fromWord + ' - ' + toWord
					if key in bigrams:
						bigrams[key][2] += 1
					else:
						bigrams[key] = [fromWord, toWord, 1]

		return (list(unigrams.values()), list(bigrams.values()))


	def addPhrases(self, phrases:list[str]):
		(unigrams, bigrams) = self.splitProcessPhrases(phrases)

		print(unigrams, bigrams)
		self.repo.addUnigrams(unigrams)
		self.repo.addBigrams(bigrams)