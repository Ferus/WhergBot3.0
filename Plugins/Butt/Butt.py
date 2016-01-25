#!/usr/bin/env python3

import random

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Butt Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "butt"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Replaces random words with `butt`")
		self.bot.config.set_safe("plugins."+self.name+".channels", [], "(list) A list of allowed channels")
		self.bot.config.set_safe("plugins."+self.name+".replyrate", 15, "(int) Percentage of replyrate, 0-100, lower = less.")
		self.bot.config.set_safe("plugins."+self.name+".maxreplaces", 2, "(int) Maximum number of replaces allowed at once.")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		message = " ".join(message.params[1:]).split()

		if origin.startswith("#"):
			if origin not in self.bot.config.get("plugins."+self.name+".channels"):
				return None

		i = random.randint(0, 100)
		if i > self.bot.config.get("plugins."+self.name+".replyrate"):
			return None

		if len(message) > 3:
			for _ in range(random.randint(1, self.bot.config.get("plugins."+self.name+".maxreplaces"))):
				word = random.choice(list(set(message)))
				for index, item in enumerate(message):
					if item == word:
						message[index] = "butt"
						break
		else:
			message.insert(random.randint(0, len(message)), "butt")
		self.bot.ircsock.say(origin, " ".join(message))
