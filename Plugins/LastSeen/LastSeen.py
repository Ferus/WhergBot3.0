#!/usr/bin/env python3

import time
import sqlite3

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Random Choice Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "lastseen"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Stores the last time a user has been seen")
		self.bot.config.set_safe("plugins."+self.name+".database_path"
			,"Plugins/LastSeen/lastseen-{self.bot.name}.sql3".format(self=self)
			,_help="(str) Path to the database, use :memory: to not save to disk"
		)
		self.bot.config.set_safe("plugins."+self.name+".blacklist", [], _help="(list) List of channels to not record")
		self.bot.config.set_safe("plugins."+self.name+".timestamp"
			,"\002%h %d, %Y\002 around \002%I:%M:%S %p\002"
			,_help="(str) Timestamp message format"
		)
		self.Seen = LastSeen(database=self.bot.config.get("plugins."+self.name+".database_path"))
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"seen" and len(message.params) > 2:
			info = self.Seen.getLastSeen(message.params[2].lower())
			if info:
				nick, chan, msg, timestamp = info
				time_format = self.bot.config.get("plugins."+self.name+".timestamp")
				timestamp = time.strftime(time_format, time.localtime(timestamp))
				self.bot.ircsock.say(origin, "\002{0}\002 was last seen in \002{1}\002 (\002{2}\002) on \002{3} UTC -8\002".format(message.params[2], chan, msg, timestamp))
			else:
				self.bot.ircsock.say(origin, "I don't know who \002{0}\002 is.".format(message.params[2]))

		if not origin.startswith("#"):
			# Dont log PM's
			return None
		if origin in self.bot.config.get("plugins."+self.name+".blacklist"):
			# Dont log blacklist
			return None

		self.Seen.addLastSeen(message.origin()[1:], origin, " ".join(message.params[1:]))


class LastSeen(object):
	def __init__(self, database=":memory:"):
		self.database = database
		self.connection = sqlite3.connect(self.database, check_same_thread=False)
		cursor = self.connection.cursor()
		cursor.execute("""CREATE TABLE IF NOT EXISTS lastseen
			(nick TEXT PRIMARY KEY
			,channel TEXT
			,last_msg TEXT
			,timestamp DATE DEFAULT (strftime('%s', 'now'))
			)"""
		)

	def getLastSeen(self, nick):
		cursor = self.connection.cursor()
		result = cursor.execute("SELECT channel, last_msg, timestamp FROM lastseen WHERE nick=?", [nick.lower()])
		try:
			channel, last_msg, timestamp = result.fetchone()
			return (nick, channel, last_msg, timestamp)
		except TypeError as e:
			return None

	def addLastSeen(self, nick, channel, last_msg):
		nick = nick.lower()
		count = self.connection.cursor()
		cursor = self.connection.cursor()
		result = count.execute("SELECT COUNT(0) FROM lastseen WHERE nick=?", [nick])
		if result.fetchone()[0] == 0:
			cursor.execute("INSERT INTO lastseen (nick, channel, last_msg) VALUES (?, ?, ?)", [nick, channel, last_msg])
		else:
			cursor.execute("UPDATE lastseen SET channel=?, last_msg=?, timestamp=strftime('%s', 'now') WHERE nick=?", [channel, last_msg, nick])
		self.connection.commit()
