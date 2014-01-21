#!/usr/bin/env python3

class Plugin(object):
	"""General Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "general"
		self.priority = 0

	def finish(self):
		pass

	def hook(self):
		return True

	def call(self, message):
		if message.command == "001":
			self.bot.ircsock.join(",".join(self.bot.config.get('channels')))
