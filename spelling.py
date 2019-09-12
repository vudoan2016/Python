import sys
import requests
import pandas as pd
import re
import random
import logging
import sqlite3
from sqlite3 import Error
import ipywidgets as widgets
from IPython.display import display, HTML
from IPython.core.interactiveshell import InteractiveShell
from bs4 import BeautifulSoup
from ipywidgets import HBox, Label

HTML('<style> .widget-hbox .widget-label { max-width:350ex; text-align:left} </style>')

SAMPLE_WORDS = 10
LOG_FILENAME = 'spelling.log'
DBASE_FILE = 'word_db.db'
excel_files = ['spelling_bee_list_grade_6.xlsx',
							 'SantaClaraSpellingList18-19.xlsx',
							 '200 words.xlsx']
book_urls = ['http://www.gutenberg.org/cache/epub/76/pg76.txt']
spelling_bee_urls = ['http://www2.sharonherald.com/herald/nie/spellb/spelllist1.html',
										 'http://www2.sharonherald.com/herald/nie/spellb/spelllist2.html',
										 'http://www2.sharonherald.com/herald/nie/spellb/spelllist3.html']

InteractiveShell.ast_node_interactivity = "all"
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', -1)

logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

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

def fetch_excels(files):
	col = []
	for f in files:
		df = pd.read_excel(f, sheet_name='Table 1')
		for index, row in df.iterrows():
			if 'Unnamed: 1' in df:
				col.append((row['Unnamed: 0'].split()[0].lower(), row['Unnamed: 1']))
			else:
				entry = row['Unnamed: 0'].replace('\n', '. ').split(':')
				col.append((entry[0].split()[0], entry[1]))
	return col

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
def analyze_collection(col, summary, count, cache):
	for word in col:
		if len(word[0]) in summary.keys() and word[0] not in cache.keys():
			summary[len(word[0])] += 1
			count += 1
		elif word[0] not in cache.keys():
			summary[len(word[0])] = 1
			count += 1

	return summary, count

# Store the collection of word-defs in the cache & database
def store_collection(col, cache, db_handle):
	for word_def in col:
		if word_def[0] not in cache.keys():
			cache[word_def[0]] = word_def[1]
			db_insert_row(db_handle, word_def)

	return cache

def display_summary(summary, total):
	counts = [total]
	headers = ['Total']
	for size, count in summary.items():
		counts.append(count)
		headers.append(str(size)+'-letter')
	display(pd.DataFrame([counts], columns=headers).style.hide_index())

def get_sample(db):
	return random.sample(db.items(), SAMPLE_WORDS)

def spell(db_file, sample):
	for word in sample:
		check_box = State(db_file, word)
		check_box.start()

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

def db_insert_row(db_handle, word_def):
	sql = 'INSERT INTO words(word, def) VALUES(?, ?)'
	try:
		curs = db_handle.cursor()
		curs.execute(sql, word_def)
	except Error as e:
		print(e)
	return curs.lastrowid # usage?

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

	if col: # empty database
		info, count = analyze_collection(col, info, count, cache)
		cache = dict(col)
	else:
		# Scrape web pages if database doesn't exist
		col = scrape_pages(spelling_bee_urls)
		info, count = analyze_collection(col, info, count, cache)
		cache = store_collection(col, cache, db_handle)

		# Fetch words from excel sheets
		col = fetch_excels(excel_files)
		# col may contain duplicates
		info, count = analyze_collection(col, info, count, cache)
		# cache should not have duplicate
		cache = store_collection(col, cache, db_handle)

	db_handle.commit()
	db_handle.close()

	display_summary(info, count)
	today = get_sample(cache)
	spell(DBASE_FILE, today)

