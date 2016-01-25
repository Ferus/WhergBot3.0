#!/usr/bin/env python3

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Next Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "next"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Next!")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"next":
			self.bot.ircsock.say(origin, "Another satisfied customer! Next!")
