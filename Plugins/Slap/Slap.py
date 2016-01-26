#!/usr/bin/env python3

import random
from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Slap Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "slap"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Slap!")
		self.bot.config.set_safe("plugins."+self.name+".fishfile", "Plugins/Slap/fish.txt", "(str) Fish to slap with")
		with open(self.bot.config.get("plugins."+self.name+".fishfile"), 'r') as fish:
			self.fish = fish.read().splitlines()
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		person = message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"slap":
			if len(message.params) > 3:
				reason = " ".join(message.params[3:])
			else:
				reason = random.choice(self.fish)

			if len(message.params) > 2:
				target = message.params[2]
			else:
				target = person

			self.bot.ircsock.action(origin, "slaps {0} around a bit with {1}.".format(target, reason))
