#!/usr/bin/env python3

import re
from plugin import BasicPlugin

from urbandict import urbandict

class Plugin(BasicPlugin):
	"""UrbanDictionary Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "urbandictionary"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "UrbanDictionary Definitions")
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"ud" and len(message.params) >= 3:
			index = 0
			term = " ".join(message.params[2:])
			if re.search(r"\d+", message.params[2]):
				index = int(message.params[2])
				term = " ".join(message.params[3:])

			defs = urbandict.define(term)
			d = defs[index] if index < len(defs) else 0
			d['word'] = d['word']
			d['def'] = d['def']
			d['example'] = d['example']
			print(d)
			string = "\002[UrbanDict]\002 {0}: {1} (Example: {2})".format(d['word'], d['def'], d['example'])
			string = re.sub(r"\n", "", string)
			string = re.sub(r"\s{2,}", " ", string)
			self.bot.ircsock.say(origin, string)
