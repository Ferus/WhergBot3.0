#!/usr/bin/env python3

import os
import re
import sqlite3
import logging

from plugin import BasicPlugin
from account import AuthorityError

logger = logging.getLogger("Quotes")

class QuotesDatabase(object):
	def __init__(self, database=":memory:"):
		def regexp(expr, item):
			reg = re.compile(expr)
			return reg.search(item, re.IGNORECASE) is not None

		self.database = database
		self.connection = sqlite3.connect(self.database, check_same_thread=False)
		self.connection.create_function("REGEXP", 2, regexp)

		cursor = self.connection.cursor()
		cursor.execute("CREATE TABLE IF NOT EXISTS quotes (id INTEGER PRIMARY KEY AUTOINCREMENT, quote TEXT)")

		try:
			cursor = self.connection.cursor()
			self.last_id = cursor.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
		except StopIteration as e:
			self.last_id = 0
		logger.info("{0} rows have been loaded.".format(self.last_id))
		self.save()

	def save(self):
		self.connection.commit()
		logger.info("Saving Database!")

	def add(self, quote):
		try:
			cursor = self.connection.cursor()
			cursor.execute("INSERT INTO quotes VALUES (NULL, ?)", (quote,))
			self.last_id = cursor.lastrowid
			self.save()
			return True
		except Exception as e:
			logger.exception(e)
			return False

	def delete(self, number):
		try:
			assert isinstance(number, int)
			cursor = self.connection.cursor()
			cursor.execute("UPDATE quotes SET quote='This quote has been deleted.' WHERE id=?", (number,))
			logger.info("Deleted quote number {0}".format(number))
			self.save()
			return True
		except Exception as e:
			logger.exception(e)
			return False

	def number(self, number):
		try:
			assert isinstance(number, int)
			if number > self.last_id:
				raise Exception()
			cursor = self.connection.cursor()
			cursor.execute("SELECT quote FROM quotes WHERE id=?", (number,))
			return cursor.fetchone()[0]
		except Exception as e:
			logger.exception(e)
			return None

	def random(self):
		cursor = self.connection.cursor()
		cursor.execute("SELECT * FROM quotes ORDER BY RANDOM () LIMIT 1")
		return cursor.fetchone()

	def count(self):
		return self.last_id

	def search(self, regexp):
		_quotes = []

		cursor = self.connection.cursor()
		cursor.execute("SELECT * FROM quotes WHERE quote REGEXP ?", (regexp,))
		for row in cursor.fetchall():
			_quotes.append(row[0])
		return _quotes

	def dump(self, backupFile="quotes.txt"):
		try:
			with open(backupFile, "w") as backup:
				cursor = self.connection.cursor()
				cursor.execute("SELECT quote FROM quotes")
				for quote in cursor.fetchall():
					backup.write(quote[0]+"\n")
			logger.info("Created backup file at {0}".format(str(backupFile)))
			return True
		except Exception as e:
			logger.exception(e)
			return False



class Plugin(BasicPlugin):
	"""Quotes Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "quotes"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Quotes database.")
		self.bot.config.set_safe("plugins."+self.name+".permission_level", 0, "(int) Permission level to add or delete quotes")
		self.bot.config.set_safe("plugins."+self.name+".database", ":memory:", "(str) Path to database (or :memory for instance only)")

		self.Quotes = QuotesDatabase(self.bot.config.get("plugins."+self.name+".database"))
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		user = self.bot.users.get_user(message.origin()[1:])

		if message.params[1] == self.bot.config.get("command_trigger")+"quote":

			if len(message.params) >= 4:
				if (message.params[2] == "search" or message.params[2] == "find"):
					regexp = " ".join(message.params[3:])
					quotes = self.Quotes.search(regexp)
					if len(quotes) >= 1:
						to_send = "I found {0} quote{1} matching the string '{2}': Quote number{1} {3}".format(
							len(quotes)
							,"s" if len(quotes) > 1 else ""
							,regexp
							,", ".join(str(y) for y in quotes)
						)
					else:
						to_send = "I didn't find any quotes matching the string '{0}': Please redefine your search.".format(regexp)


				elif message.params[2] == "add":
					if user.account.auth.get("level") > self.bot.config.get("plugins."+self.name+".permission_level") or \
						not user.account.auth.get("authenticated"):
						raise AuthorityError(self.bot, user.nick, "You do not have permission to access this command")

					newquote = " ".join(message.params[3:])
					if self.Quotes.add(newquote):
						to_send = "Added new quote number {0} successfully!".format(self.Quotes.count())

				elif message.params[2] == "del":
					if user.account.auth.get("level") > self.bot.config.get("plugins."+self.name+".permission_level") or \
						not user.account.auth.get("authenticated"):
						raise AuthorityError(self.bot, user.nick, "You do not have permission to access this command")
					if isinstance(int(message.params[3]), int):
						if self.Quotes.delete(int(message.params[3])):
							to_send = "Deleted quote number {0} successfully".format(message.params[3])


			elif len(message.params) >= 3:
				if re.search(r"\d+", message.params[2]):
					quote = self.Quotes.number(int(message.params[2]))
					to_send = quote if quote else "That quote does not exist."

				elif message.params[2] == "count":
					to_send = "I currently hold {0} quotes in my database.".format(self.Quotes.count())

				elif message.params[2] == "backup":
					to_send = "Created backup." if self.Quotes.dump("Plugins/Quotes/quotes-{0}.txt".format(self.bot.name)) else "Backup errored."

			elif len(message.params) == 2:
				quote_id, quote_str = self.Quotes.random()
				to_send = "Quote #\002{0}\002: {1}".format(quote_id, quote_str)

			self.bot.ircsock.say(origin, to_send)



