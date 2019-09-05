import requests
import pandas as pd
import re
import random
import shelve
import time
import os
import logging
import docx
import PyPDF2
import ipywidgets as widgets
from IPython.display import display, HTML
from IPython.core.interactiveshell import InteractiveShell
from bs4 import BeautifulSoup
from ipywidgets import HBox, Label

HTML('<style> .widget-hbox .widget-label { max-width:350ex; text-align:left} </style>')

TODAY_WORD_COUNT = 10
LOG_FILENAME = 'spelling.log'

book_urls = ['http://www.gutenberg.org/cache/epub/76/pg76.txt']
spelling_bee_urls = ['http://www2.sharonherald.com/herald/nie/spellb/spelllist1.html',
										 'http://www2.sharonherald.com/herald/nie/spellb/spelllist2.html',
										 'http://www2.sharonherald.com/herald/nie/spellb/spelllist3.html']

InteractiveShell.ast_node_interactivity = "all"
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', -1)
#pd.set_option('max_colwidth', 1000)
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

class State:
	def __init__(self, word_db, word):
		self.word_db = word_db
		self.word = word
		self.c_box = widgets.Checkbox(False)

	def action(self, *args):
		if self.c_box.value:
			lst = self.word_db[str(len(self.word[0]))]
			lst.remove(self.word)
			if lst:
				self.word_db[str(len(self.word[0]))] = lst
			else:
				del(self.word_db[str(len(self.word[0]))])

	def start(self):
		display(HBox([self.c_box, Label(self.word[1])]))
		self.c_box.observe(self.action, 'value')

def extact_docx(file):
	doc = docx.Document(file)
	full_txt = []
	for pars in doc.paragraphs:
		full_txt.append(pars.text)
	return '\n'.join(full_txt)

def extract_pdf(file):
	obj = open(file, 'rb')
	pdf_reader = PyPDF2.PdfFileReader(obj)
	page = pdf_reader.getPage(2)
	print(page.extractText())

def extract_excel(file):
	df = pd.read_excel(file, sheet_name='Table 1')
	return [(row['Unnamed: 0'], row['Unnamed: 1']) for index, row in df.iterrows()]

def scrape_page(url, count):
	page = requests.get(url)
	soup = BeautifulSoup(page.text, 'html.parser')
	table = soup.find_all('table')[1] # words are in 2nd table
	words = []
	for row in table.find_all('b'):
		words.append((row.contents[0].lower(), row.next_sibling))
		count += 1
		#words.append(row.contents[0] for row in table.find_all('b'))
	return words, count

def get_book(url, count):
	words = []

	page = requests.get(url)
	beginning = False
	for line in page.text.splitlines():
		line = line.strip()
		if line:
			if line == 'CHAPTER I.':
				beginning = True

			if not beginning:
				continue

			if 'THE END.' in line:
				break

			for word in re.split(';| |\.|,|--|"|_|\'|\?|\)|:|\(|\!|]', line):
				#w = word.translate(str.maketrans('', '', string.punctuation))
				w = word.strip().lower()
				if '-' not in w and len(w) > 4 and not w.isnumeric() and (w, '') not in words:
					words.append((w, ''))
					count += 1
				'''
				if w not in ignores:
					words.append(w)
				'''
	return words, count

# print(sorted(list(frequency.items()), key=lambda tup: tup[1], reverse=True)[:20])
def analyze_book(book, word_bank):
	for word_def in book:
		if len(word_def[0]) in word_bank.keys() and word_def[0] not in word_bank:
			word_bank[len(word_def[0])].append(word_def)
		else:
			word_bank[len(word_def[0])] = [word_def]
	return word_bank

def display_book_info(info, total):
	summary = [total]
	headers = ['Total']
	for size, l in info.items():
		summary.append(len(l))
		headers.append(str(size)+'-letter')
	display(pd.DataFrame([summary], columns=headers))

def today_words(info):
	today = []
	for length in random.sample(info.keys(), TODAY_WORD_COUNT):
		today.append(random.choice(info[length]))
	return today

def spell(word_db, today):
	for word in today:
		c_box = State(word_db, word)
		c_box.start()

if __name__ == '__main__':
	count = 0
	word_bank = {}

	# Loading databases
	if os.path.exists('word_dict.dat'):
		word_db = shelve.open('word_dict')
		start = time.time()
		for key in word_db:
			word_bank[int(key)] = []
			for item in word_db[key]:
				word_bank[int(key)].append(item)
			count += len(word_db[key])
		logging.debug('Loading database takes %d', time.time() - start)
	else:
		start = time.time()
		# Scrape web pages if database doesn't exist
		if not word_bank:
			for url in spelling_bee_urls:
				book, count = scrape_page(url, count)
				word_bank = analyze_book(book, word_bank)
		logging.debug('Scraping takes %d', time.time() - start)

		book = extract_excel('SantaClaraSpellingList18-19.xlsx')
		word_bank = analyze_book(book, word_bank)
		count += len(book)

		'''
		for url in book_urls:
			book, count = get_book(url, count)
			word_bank = analyze_book(book, word_bank)
		'''

		word_db = shelve.open('word_dict')
		for key in word_bank:
			word_db[str(key)] = []
			for item in word_bank[key]:
				word_db[str(key)].append(item)

	display_book_info(word_bank, count)
	today = today_words(word_bank)
	spell(word_db, today)
