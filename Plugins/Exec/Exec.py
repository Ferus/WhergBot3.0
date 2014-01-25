#!/usr/bin/env python3

"""
Exec Plugin

Runs raw commands in python by (ab)using exec()
"""

class Plugin(object):
	"""Exec Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "exec"
		self.priority = 0

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe(self.name, None, _help="Exec executes a given python string")
		self.bot.config.set_safe("exec.allowed"
			, ["Ferus!anonymous@the.interwebs"]
			, _help="(list) Holds a list of full IRC hostmasks (nick!ident@host) " \
			"of people who are allowed to use the !exec command")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None
		if message.params[1] == "!exec":
			if message.prefix[1:] in self.bot.config.get("exec.allowed"):
				try:
					exec(' '.join(message.params[2:]))
				except Exception as e:
					self.bot.ircsock.say(message.params[0], repr(e))
			else:
				self.bot.ircsock.notice(message.origin()[1:], "You are not authorized to use this command!")
