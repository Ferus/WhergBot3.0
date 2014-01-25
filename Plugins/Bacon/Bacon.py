#!/usr/bin/env python3

class Plugin(object):
	"""Bacon Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "bacon"
		self.priority = 0

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe(self.name, None, "To cook bacon for someone, use @bacon")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None
		if message.params[1] == "@bacon":
			target = ' '.join(message.params[2:]) if len(message.params) >= 3 else "Ferus"
			self.bot.ircsock.action(message.params[0], "cooks up some fancy bacon for {0}".format(target))
