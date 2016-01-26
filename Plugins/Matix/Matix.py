#!/usr/bin/env python3

import os
import logging
from random import choice

from plugin import BasicPlugin
from account import AuthorityError

logger = logging.getLogger("Matix")

class Plugin(BasicPlugin):
	"""Matix Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "matix"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "matix has u")
		self.bot.config.set_safe("plugins."+self.name+".directory", "Plugins/Matix/Spams/", "(str) Directory with the files")
		self.bot.config.set_safe("plugins."+self.name+".permission_level", 0, "(int) Permission level for matix")
		self.bot.config.set_safe("plugins."+self.name+".require_oper", True, "(bool) Whether bot should require oper perms to use this")
		self.files = os.listdir(self.bot.config.get("plugins."+self.name+".directory"))
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		user = self.bot.users.get_user(message.origin()[1:])

		if message.params[1] == self.bot.config.get("command_trigger")+"matix":
			if self.bot.config.get("plugins."+self.name+".require_oper"):
				if not self.bot.is_oper:
					return None

			if user.account.auth.get("level") > self.bot.config.get("plugins."+self.name+".permission_level") and \
				user.account.auth.get("authenticated"):
				raise AuthorityError(self.bot, user.nick, "You do not have permission to access this command")

			if len(message.params) > 2:
				file = message.params[2] if message.params[2] in self.files else choice(self.files)
				with open("{0}/{1}".format(self.bot.config.get("plugins."+self.name+".directory"), file)) as f:
					try:
						for line in f.readlines():
							self.bot.ircsock.say(origin, line)
					except UnicodeDecodeError:
						self.files.remove(file)
						os.unlink(self.bot.config.get("plugins."+self.name+".directory") + os.sep + file)
						logger.exception("Removing invalid unicode file: {0}".format(file))

