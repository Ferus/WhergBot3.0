#!/usr/bin/env python3

# TODO Formatting and stuff, this is just temp

class Plugin(object):
	"""PrettyPrinter - Fancy console output."""
	def __init__(self, bot):
		self.bot = bot
		self.name = "prettyprinter"
		self.priority = 50

	def finish(self):
		pass

	def hook(self):
		return True

	def call(self, message):
		# Refuck text to print
		if len(message.params) == 2:
			message.params.append(" ".join(message.params.pop(1)))
		print("\033[31m[Bot: {0}] \033[32m{1}\033[0m".format(self.bot.name, repr(message)))
		# Unfuck text before it's refucked
		if len(message.params) == 2:
			message.params.append(message.params.pop(1).split(" "))
