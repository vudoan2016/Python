import sys
import requests
import pandas as pd
import re
import random
import logging
import docx
import PyPDF2
import sqlite3
from sqlite3 import Error
import ipywidgets as widgets
from IPython.display import display, HTML
from IPython.core.interactiveshell import InteractiveShell
from bs4 import BeautifulSoup
from ipywidgets import HBox, Label

HTML('<style> .widget-hbox .widget-label { max-width:350ex; text-align:left} </style>')

TODAY_WORD_COUNT = 10
LOG_FILENAME = 'spelling.log'
DBASE_FILE = 'word_db.db'
EXCEL = 'SantaClaraSpellingList18-19.xlsx'

book_urls = ['http://www.gutenberg.org/cache/epub/76/pg76.txt']
spelling_bee_urls = ['http://www2.sharonherald.com/herald/nie/spellb/spelllist1.html',
										 'http://www2.sharonherald.com/herald/nie/spellb/spelllist2.html',
										 'http://www2.sharonherald.com/herald/nie/spellb/spelllist3.html']

InteractiveShell.ast_node_interactivity = "all"
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', -1)

logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

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

class State:
	def __init__(self, db_file, word):
		self.db_file = db_file
		self.word = word
		self.c_box = widgets.Checkbox(False, description=word[0])

	def action(self, change):
		if self.c_box.value:
			sql = 'DELETE FROM words WHERE word=?'
			try:
				db_handle = db_connect(self.db_file)
				curs = db_handle.cursor()
				curs.execute(sql, (self.word[0],))
				db_handle.commit()
				db_handle.close()
			except Error as e:
				print(e)

	def start(self):
		display(HBox([self.c_box, Label(self.word[1])]))
		self.c_box.observe(self.action, 'value')

def extract_excel(file):
	df = pd.read_excel(file, sheet_name='Table 1')
	return [(row['Unnamed: 0'], row['Unnamed: 1']) for index, row in df.iterrows()]

def scrape_pages(urls):
	col = []
	for url in spelling_bee_urls:
		page = requests.get(url)
		soup = BeautifulSoup(page.text, 'html.parser')
		table = soup.find_all('table')[1] # words are in 2nd table
		for row in table.find_all('b'):
			col.append((row.contents[0].lower(), row.next_sibling))
	return col

# print(sorted(list(frequency.items()), key=lambda tup: tup[1], reverse=True)[:20])
def analyze_collection(col, info, count, db):
	for word in col:
		if len(word[0]) in info.keys() and word[0] not in db.keys():
			info[len(word[0])] += 1
			count += 1
		elif word[0] not in db.keys():
			info[len(word[0])] = 1
			count += 1

	return info, count

def store_collection(col, cache, db_handle):
	for word in col:
		if word[0] not in cache.keys():
			cache[word[0]] = word[1]
			db_insert_row(db_handle, word)

			#shelve_db[word[0]] = word[1]
	return cache

def display_info(info, total):
	summary = [total]
	headers = ['Total']
	for size, count in info.items():
		summary.append(size)
		headers.append(str(size)+'-letter')
	display(pd.DataFrame([summary], columns=headers).style.hide_index())

def today_words(db):
	return random.sample(db.items(), TODAY_WORD_COUNT)

def spell(db_file, today):
	for word in today:
		c_box = State(db_file, word)
		c_box.start()

def db_connect(db_file):
	db_handle = None
	try:
		db_handle = sqlite3.connect(db_file)
	except Error as e:
		print(e)

	return db_handle

def db_table_create(db_handle):
	try:
		cursor = db_handle.cursor()
		cursor.execute('CREATE TABLE IF NOT EXISTS words (word text, def text)')
	except Error as e:
		print(e)

def db_insert_row(db_handle, word):
	sql = 'INSERT INTO words(word, def) VALUES(?, ?)'
	try:
		c = db_handle.cursor()
		c.execute(sql, word)
	except Error as e:
		print(e)
	return c.lastrowid

def db_load(db_handle):
	try:
		cursor = db_handle.cursor()
		cursor.execute('SELECT * FROM words')
	except Error as e:
		print(e)
	return cursor.fetchall()

if __name__ == '__main__':
	db_handle = db_connect(DBASE_FILE)
	if not db_handle:
		sys.exit()

	db_table_create(db_handle)

	# Loading databases
	col = db_load(db_handle)

	count = 0
	cache = {}
	info = {}

	if col:
		info, count = analyze_collection(col, info, count, cache)
		cache = dict(col)
	else:
		# Scrape web pages if database doesn't exist
		col = scrape_pages(spelling_bee_urls)
		info, count = analyze_collection(col, info, count, cache)
		cache = store_collection(col, cache, db_handle)

		col = extract_excel(EXCEL)
		info, count = analyze_collection(col, info, count, cache)
		cache = store_collection(col, cache, db_handle)

	db_handle.commit()
	db_handle.close()

	display_info(info, count)
	today = today_words(cache)
	spell(DBASE_FILE, today)

