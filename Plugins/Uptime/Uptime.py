#!/usr/bin/env python3

import time
import datetime
from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Uptime Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "uptime"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Uptime")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"uptime":
			uptime = time.time() - self.bot.time
			uptime = datetime.timedelta(seconds=uptime)
			self.bot.ircsock.say(origin, "Current uptime is: {0}.".format(str(uptime).split(".")[0].zfill(8)))
