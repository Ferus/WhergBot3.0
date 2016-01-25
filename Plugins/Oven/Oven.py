#!/usr/bin/env python3

from threading import Timer
from random import randint

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Oven Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "oven"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Oven all the things")
		self.bot.config.set_safe("plugins."+self.name+".time_min", 7, _help="(int) Minimum time to wait")
		self.bot.config.set_safe("plugins."+self.name+".time_max", 11, _help="(int) Maximum time to wait")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"oven" and len(message.params) > 2:
			self.bot.ircsock.action(origin, "prepares his ovens")
			wait_time = randint(self.bot.config.get("plugins."+self.name+".time_min")
				,self.bot.config.get("plugins."+self.name+".time_max")
			)
			t = Timer(wait_time, self.bot.ircsock.action, (origin, "ovens {0}".format(" ".join(message.params[2:]))))
			t.daemon = True
			t.start()
