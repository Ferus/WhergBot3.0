#!/usr/bin/env python3

import re
import time
import html
import json
import sqlite3
import requests

from plugin import BasicPlugin
from utils import truncate

WIKIPEDIA_URL_RE = re.compile(r"(?:https?:\/\/)?en.wikipedia\.org\/wiki\/.*?(?:\s|$)")

class Plugin(BasicPlugin):
	"""Wikipedia Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "wikipedia"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Wikipedia.")
		self.bot.config.set_safe("plugins."+self.name+".database", "Plugins/Wikipedia/wikicache.sql3", "(str) Cache database location.")
		self.bot.config.set_safe("plugins."+self.name+".cachetime", 60*60*60*24*7, "(int) How long to cache pages.")
		self.wiki = WikipediaAPIWrapper(Database=self.bot.config.get("plugins."+self.name+".database"))
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"wiki" and len(message.params) >= 3:
			article = self.wiki.searchWikipediaForArticles(" ".join(message.params[2:]))
			try:
				article, title, timestamp = self.wiki.getArticleFromDatabase(article)
			except ArticleNotInDatabase:
				article, title, timestamp = self.wiki.getArticleFromWikipedia(article)
			article = truncate(article['description'])
			self.bot.ircsock.say(origin, "\x02[Wikipedia]\x02 {0} - https://en.wikipedia.org/wiki/{1}".format(article, title.replace(" ", "_")))

		else:
			for word in message.params[1:]:
				if WIKIPEDIA_URL_RE.search(word):
					article = word.split('/')[-1]
					section = ""
					if "#" in article:
						article, section = article.split("#")
					article = self.wiki.searchWikipediaForArticles(article)
					try:
						article = self.wiki.getArticleFromDatabase(article)
					except ArticleNotInDatabase:
						article = self.wiki.getArticleFromWikipedia(article)
					article = article[0]
					if section != "":
						article = truncate(article[section])
					else:
						article = truncate(article['description'])
					self.bot.ircsock.say(origin, "\x02[Wikipedia]\x02 {0}".format(article))

class ArticleNotInDatabase(Exception):
	"""Basic Exception class, for now."""
	pass

class ArticleNotInWikipedia(Exception):
	"""Another Exception class."""
	pass

class WikipediaAPIWrapper(object):
	"""An API Wrapper for Wikipedia that caches results.
	It's better than polling and parsing HTML.
	"""
	def __init__(self, Database = 'Wiki.db', Cachetime = 60*60*60*24*7):
		self._db = Database
		self.Cachetime = Cachetime
		self.DBConnection = sqlite3.connect(self._db, check_same_thread = False)
		self.DBCursor = self.DBConnection.cursor()
		self.DBCursor.execute("CREATE TABLE IF NOT EXISTS Wikipedia (timestamp INTEGER, article_name TEXT, article_extract TEXT)")

	@property
	def __time__(self):
		return time.time()

	def compareTimestamps(self, timestamp):
		"""Compare the cached timestamp to current time.
		Returns False if expired, True otherwise.
		"""
		if self.__time__() > timestamp + self.Cachetime:
			return False
		return True

	def checkIfArticleInDatabase(self, article):
		"""Checks if an article exists.
		"""
		article_extract = self.DBCursor.execute("SELECT article_extract FROM Wikipedia WHERE article_name=?", (article,))
		article_extract = article_extract.fetchone()
		if article_extract is None:
			return False
		return True

	def searchWikipediaForArticles(self, article):
		"""Pass an article name to wikipedias search API, return the first result.
		"""
		request = requests.get("https://en.wikipedia.org/w/api.php?action=opensearch&limit=3&namespace=0&format=json&search={0}".format(article))
		request.raise_for_status()
		request = json.loads(request.text)
		return request[1][0]

	def getArticleFromDatabase(self, article):
		"""Poll the database for an article, if it's not found, raise ArticleNotInDatabase Error
		"""
		if self.checkIfArticleInDatabase(article) == False:
			raise ArticleNotInDatabase("The requested article wasn't found in the database.")
		query = self.DBCursor.execute("SELECT article_extract, article_name, timestamp FROM Wikipedia WHERE article_name=?", (article,))
		article_extract, title, timestamp = query.fetchone()
		article_extract = json.loads(article_extract)
		return (article_extract, title, timestamp)

	def getArticleFromWikipedia(self, article):
		"""Poll the Wikipedia API for an article and cache it.
		Should be called if getArticleFromDatabase() raises ArticleNotInWikipedia Error.
		"""
		request = requests.get("http://en.wikipedia.org/w/api.php?action=query&format=json&exinfo=1&prop=extracts&redirects=0&titles={0}".format(article))
		# HTTP Errors should be handled outside of here
		request.raise_for_status()
		request = html.unescape(request.text)
		request = json.loads(request)
		# dirty hack, since I don't know how to get unknown keys from a dict
		for key in request['query']['pages'].keys():
			# we assume theres only one id
			if key == "-1":
				raise ArticleNotInWikipedia("The requested article was not found on Wikipedia's site.")
			data = request['query']['pages'][key]
			break
		title = replacetags(data.get('title'))
		extract = data.get('extract').replace("\n", "")
		article_extract = {}
		# Don't parse HTML with regex, they said.
		# It'll be easy, I said.
		for subsection in re.findall(r"""
			</?h[2-5]>\s         # Match beginning <h> tag
			([\w\s]+)            # Match text inside <h> tag
			</?h[2-5]>           # Match end <h> tag
			<p>([\w<>].+?)</p>   # Match all text in proceeding <p> tag
			""", extract, re.X):
			# subsection[0] == sub name
			# subsection[1] == text
			article_extract[subsection[0].replace(" ", "_")] = replacetags(subsection[1])
		article_extract['description'] = replacetags(re.findall(r"<p>([\w<>].+?)</p>", extract)[0])
		#sqlite cant handle dicts; convert back to json
		article_extract_json = json.dumps(article_extract)
		timestamp = self.__time__
		self.DBCursor.execute("INSERT INTO Wikipedia (timestamp, article_name, article_extract) VALUES (?, ?, ?)",
			(timestamp, title, article_extract_json))
		with self.DBConnection:
			try:
				self.DBConnection.commit()
			except Exception as e:
				print(repr(e))
		return (article_extract, title, timestamp)

def replacetags(text):
	text = re.sub("</?i>", "\x1F", text)
	text = re.sub("</?b>", "\x02", text)
	return text

