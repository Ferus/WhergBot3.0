#!/usr/bin/env python3

"""
Exec Plugin

Runs raw commands in python by (ab)using exec()
"""

import logging
logger = logging.getLogger("Exec")

from plugin import BasicPlugin
from account import AuthorityError

class Plugin(BasicPlugin):
	"""Exec Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "exec"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, _help="Exec executes a given python string")
		self.bot.config.set_safe("plugins."+self.name+".permission_levels.exec"
			,0
			,_help="(int) Required level to exec raw python"
		)
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		user = self.bot.users.get_user(message.origin()[1:])

		if message.params[1] == self.bot.config.get("command_trigger")+"exec":
			if user.account.auth.get("level") > self.bot.config.get("plugins."+self.name+".permission_levels.exec") or \
				not user.account.auth.get("authenticated"):
				raise AuthorityError(self.bot, user.nick, "You do not have permission to access this command")

			try:
				exec(' '.join(message.params[2:]))
			except Exception as e:
				self.bot.ircsock.say(origin, repr(e))
