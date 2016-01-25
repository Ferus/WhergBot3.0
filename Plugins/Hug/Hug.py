#!/usr/bin/env python3

import re

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Hug Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "hug"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Hugs for everyone, maybe.")
		self.bot.config.set_safe("plugins."+self.name+".allowed_level", 50, _help="(int) Default level to allow hugs")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		nick = message.origin()[1:]
		user = self.bot.users.get_user(nick)
		message = " ".join(message.params[1:])
		if re.search(r'(?:^|\s+);[_-~\.]{1};(?:\s|$)', message):
			if user.account.auth.get("level") > self.bot.config.get("plugins."+self.name+".allowed_level"):
				self.bot.ircsock.action(origin, "kicks {0} in the balls for not being a man.".format(nick))
			else:
				self.bot.ircsock.action(origin, "hugs {0}.".format(nick))
