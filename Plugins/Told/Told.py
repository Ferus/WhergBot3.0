#!/usr/bin/env python3

import random
from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Told Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "told"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Get told!")
		self.bot.config.set_safe("plugins."+self.name+".toldfile", "Plugins/Told/told.txt", "(str) Location of the toldfile.")

		with open(self.bot.config.get("plugins."+self.name+".toldfile"), 'r') as told:
			self.told = told.read().splitlines()
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"told":
			self.bot.ircsock.say(origin, random.choice(self.told))
