#!/usr/bin/env python

"""
Help Plugin

Provides @help for all plugins and config settings
"""

import re

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	def __init__(self, bot):
		self.bot = bot
		self.name = "help"
		self.priority = 50
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, _help="Provides @help for all plugins and config settings")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		if message.params[1] == self.bot.config.get("command_trigger")+"help":
			# incase of PM's
			target = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

			if not len(message.params) > 2:
				self.bot.ircsock.say(target, "`@help <target>` where target may be a plugin name or a config setting")
				return None
			term = message.params[2]

			# TODO Fuzzy search (*) in term

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
