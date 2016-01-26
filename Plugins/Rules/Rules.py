#!/usr/bin/env python3

import os
import re
import sqlite3
import logging

from plugin import BasicPlugin

logger = logging.getLogger("Rules")

class RulesDatabase(object):
	def __init__(self, database=":memory:"):
		self.database = database
		self.connection = sqlite3.connect(self.database, check_same_thread=False)

		cursor = self.connection.cursor()
		cursor.execute("CREATE TABLE IF NOT EXISTS rules (id INTEGER PRIMARY KEY AUTOINCREMENT, rule TEXT)")

		try:
			cursor = self.connection.cursor()
			self.last_id = cursor.execute("SELECT COUNT(*) FROM rules").fetchone()[0]
		except StopIteration as e:
			self.last_id = 0
		logger.info("{0} rows have been loaded.".format(self.last_id))
		self.save()

	def save(self):
		self.connection.commit()
		logger.info("Saving Database!")

	def number(self, number):
		try:
			assert isinstance(number, int)
			if number > self.last_id:
				raise Exception()
			cursor = self.connection.cursor()
			cursor.execute("SELECT rule FROM rules WHERE id=?", (number,))
			return cursor.fetchone()[0]
		except Exception as e:
			logger.exception(e)
			return None

	def random(self):
		cursor = self.connection.cursor()
		cursor.execute("SELECT * FROM rules ORDER BY RANDOM () LIMIT 1")
		return cursor.fetchone()


class Plugin(BasicPlugin):
	"""Rules Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "rules"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Rules database.")
		self.bot.config.set_safe("plugins."+self.name+".database", "Plugins/Rules/Rules.sql3", "(str) Path to database")
		self.Rules = RulesDatabase(self.bot.config.get("plugins."+self.name+".database"))
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		user = self.bot.users.get_user(message.origin()[1:])

		if message.params[1] == self.bot.config.get("command_trigger")+"rule":

			if len(message.params) >= 3:
				if re.search(r"\d+", message.params[2]):
					rule = self.Rules.number(int(message.params[2]))
					to_send = rule if rule else "That rule does not exist."

				elif message.params[2] == "count":
					to_send = "I currently hold {0} rules in my database.".format(self.Rules.last_id)

			elif len(message.params) == 2:
				rule_id, rule_str = self.Rules.random()
				to_send = rule_str

			self.bot.ircsock.say(origin, to_send)



