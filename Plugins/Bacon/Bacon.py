#!/usr/bin/env python3

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Bacon Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "bacon"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "To cook bacon for someone, use @bacon")
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"bacon":
			target = ' '.join(message.params[2:]) if len(message.params) >= 3 else "Ferus"
			self.bot.ircsock.action(origin, "cooks up some fancy bacon for {0}".format(target))
