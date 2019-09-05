import requests
import string
import pandas as pd
import re
from IPython.display import display

pd.set_option('display.max_rows', 1000)

auxiliary_verbs = ['did', 'had', 'was']
conjunctions = ['and', 'but', 'so', 'for', 'but', 'as']
articles = ['the', 'a', 'an']
propositions = ['to', 'at', 'of', 'between']
personal_pronouns = ['he', 'I', 'you', 'me', 'him', 'her', 'they', 'them', 'it', 'we', 'us']

urls = {'Adventures of Huckleberry Finn' : 'http://www.gutenberg.org/cache/epub/76/pg76.txt'}

def get_book(title):
	url = urls[title]
	page = requests.get(url)
	words = []
	#ignores = zip(auxiliary_verbs, conjunctions, articles, propositions, personal_pronouns)
	for line in page.text.splitlines():
		if line.strip():
			for w in re.split(';| |\.|,|--|"|_|\'|\?|\)|:|\(|\!', line):
				#w = word.translate(str.maketrans('', '', string.punctuation))
				if w.strip() not in words:
					words.append(w.strip())
				'''
				if w not in ignores:
					words.append(w)
				'''
	return words

def analyze_book(book):
	words_by_length = {}
	for word in book:
		if len(word) in words_by_length:
			words_by_length[len(word)].append(word)
		else:
			words_by_length[len(word)] = [word]

	#print(sorted(list(frequency.items()), key=lambda tup: tup[1], reverse=True)[:20])

	return words_by_length

def display_book_info(info):
	for length, words in info.items():
		if length >= 4:
			display(pd.DataFrame(words, columns=[str(length)+'-words']))

if __name__ == '__main__':
	book = get_book('Adventures of Huckleberry Finn')
	info = analyze_book(book)
	display_book_info(info)
