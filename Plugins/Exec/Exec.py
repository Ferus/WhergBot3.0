#!/usr/bin/env python3

"""
Exec Plugin

Runs raw commands in python by (ab)using exec()
"""

import logging
logger = logging.getLogger("Exec")

from plugin import BasicPlugin

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
		self.bot.config.set_safe(self.name, None, _help="Exec executes a given python string")
		if not self.bot.config.get("permissions.owner"):
			self.bot.config.set_safe("permissions.owner", [],
				_help="(list) Holds a list of full IRC hostmasks (nick!ident@host) " \
				"of people who are allowed to use owner commands")
		if not self.bot.config.get("permissions.exec"):
			self.bot.config.set_safe("permissions.exec", self.bot.config.get("permissions.owner", []),
				_help="(list) Holds a list of full IRC hostmasks (nick!ident@host) " \
				"of people who are allowed to use the @exec command")
		if self.bot.config.get("permissions.exec") == []:
			logger.info("Please insert your full IRC hostmask (nick!ident@host) "\
				"in the config (permissions.exec) to use this plugin")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"exec":
			if message.prefix[1:] in self.bot.config.get("permissions.owner") or \
				message.prefix[1:] in self.bot.config.get("permissions.exec"):
				try:
					exec(' '.join(message.params[2:]))
				except Exception as e:
					self.bot.ircsock.say(origin, repr(e))
			else:
				self.bot.ircsock.notice(message.origin()[1:], "You are not authorized to use this command!")
