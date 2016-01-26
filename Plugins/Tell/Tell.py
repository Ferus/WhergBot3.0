#!/usr/bin/env python3

import sqlite3

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Tell Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "tell"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Tell a user a message.")
		self.bot.config.set_safe("plugins."+self.name+".database", "Plugins/Tell/tell.sql3", "(str) Tell database.")
		self.connection = sqlite3.connect(self.bot.config.get("plugins."+self.name+".database"), check_same_thread=False)
		cursor = self.connection.cursor()
		cursor.execute('CREATE TABLE IF NOT EXISTS tell ('
			'id INTEGER PRIMARY KEY AUTOINCREMENT,'
			'name TEXT,'
			'message TEXT,'
			'origin TEXT)'
		)
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		person = message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"tell" and len(message.params) >= 4:
			target = message.params[2]
			string = " ".join(message.params[3:])
			self.add(target, string, person)
			self.bot.ircsock.say(origin, "Your message has been sent! {0} will see it the next time I see them.".format(target))

		else:
			cursor = self.connection.cursor()
			cursor.execute("SELECT COUNT(id), origin FROM tell WHERE name=? GROUP BY origin", [person.lower()])
			counts = cursor.fetchall()
			if not counts:
				return None
			for count in counts:
				self.bot.ircsock.say(person, "You have \002{0}\002 new message{1} from \002{2}\002.".format(
					count[0], "" if count[0] == 1 else "s", count[1]))
				messages = self.getOrigin(count[1])
				for message in messages:
					self.bot.ircsock.say(person, "{0}: {1}".format(message[2], message[1]))
					cursor2 = self.connection.cursor()
					cursor2.execute("DELETE FROM tell WHERE id=?", [message[0]])
			self.connection.commit()


	def add(self, name, message, origin):
		cursor = self.connection.cursor()
		cursor.execute("INSERT INTO tell (name, message, origin) VALUES (?, ?, ?)", [name.lower(), message, origin])
		self.connection.commit()

	def getName(self, name):
		cursor = self.connection.cursor()
		cursor.execute("SELECT id, message, origin FROM tell WHERE name=?", [name.lower()])
		return cursor.fetchall()

	def getOrigin(self, origin):
		cursor = self.connection.cursor()
		cursor.execute("SELECT id, message, origin FROM tell WHERE origin=?", [origin])
		return cursor.fetchall()
