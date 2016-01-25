#!/usr/bin/env python3

from random import choice

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Random Choice Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "choice"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe(self.name, None, "Picks a random item from a comma delimited list")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"random" and len(message.params) > 2:
			self.bot.ircsock.say(origin, choice(message.params[2].split(",")))
