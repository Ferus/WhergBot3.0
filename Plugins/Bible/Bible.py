#!/usr/bin/env python

import sqlite3

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	def __init__(self, bot):
		self.bot = bot
		self.name = "bible"
		self.priority = 0
		self.load_priority = 10


	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe(self.name, None, "Provides the King James v3 Bible")
		self.bot.config.set_safe("plugins.bible.database", "Plugins/Bible/King_James_Bible.sql3", "(str) Path to the sqlite3 King James Bible file")

		self.connection = sqlite3.connect(self.bot.config.get("plugins.bible.database"), check_same_thread = False)
		self.valid_books = []
		cursor = self.connection.cursor()
		books = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
		for book in books:
			self.valid_books.append(book[0].lower())
		del cursor
		del books
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"bible" and len(message.params[2:]) == 2:
			book = message.params[2]
			chapter, verse_id = message.params[3].split(":")
			verse = self.getBibleVerse(book, chapter, verse_id)
			self.bot.ircsock.say(origin, "\002[Bible]\002 {0}".format(verse.replace("God", "\002God\002")))


	def getBibleVerse(self, book, chapter, verse_id):
		cursor = self.connection.cursor()
		verse = cursor.execute("SELECT verse_text FROM {0} WHERE chapter=? AND verse_id=?".format(book.lower().capitalize()), [chapter, verse_id]).fetchone()
		return verse[0]
