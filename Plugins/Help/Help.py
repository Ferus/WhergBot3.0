#!/usr/bin/env python

"""
Help Plugin

Provides @help for all plugins and config settings
"""

import re

class Plugin(object):
	def __init__(self, bot):
		self.bot = bot
		self.name = "help"
		self.priority = 50

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe(self.name, None, _help="Provides @help for all plugins and config settings")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		if message.params[1] == "@help":
			# incase of PM's
			target = message.params[0] if message.params[0] != self.bot.config.get('nickname') else message.origin()[1:]
			term = message.params[2]

			if term in self.bot.config:
				_help = self.bot.config.get_help(term)
				if re.search(r"(^\(\S+?\))", _help):
					# config option help
					# > If there are capturing groups in the separator and it matches at the
					# start of the string, the result will start with an empty string.
					# gg re.split()
					null, _type, _help = re.split(r"(^\(\S+?\)) ", _help, 1)
					self.bot.ircsock.say(target, "Help for option {0}: \x0304{1}\x03 {2}".format(term, _type, _help))
				else:
					# plugin help
					self.bot.ircsock.say(target, "Help for plugin {0}: {1}".format(term, _help))
			else:
				# easter egg command - @help <nick>
				self.bot.ircsock.say(target, "No help available for {0}".format(term))
