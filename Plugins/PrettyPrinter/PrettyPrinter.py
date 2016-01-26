#!/usr/bin/env python3

# TODO Formatting and stuff, this is just temp
# See github for new version?
# https://github.com/Ferus/WhergBot3.0/blob/master/Plugins/PrettyPrinter/PrettyPrinter.py

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""PrettyPrinter - Fancy console output."""
	def __init__(self, bot):
		self.bot = bot
		self.name = "prettyprinter"
		self.priority = 50
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "pretty prints a formatted IRC message to the controlling terminal")
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		print("\033[31m[Bot: {0}] \033[32m{1}\033[0m".format(self.bot.name, repr(message)))
