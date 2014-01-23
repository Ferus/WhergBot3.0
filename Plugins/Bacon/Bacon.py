#!/usr/bin/env python3

class Plugin(object):
	"""Bacon Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "Bacon"
		self.priority = 0

	def finish(self):
		pass

	def hook(self):
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None
		if message.params[1][0] == "@bacon":
			self.bot.ircsock.action(message.params[0], "cooks up some fancy bacon for {0}".format(message.params[1][1]))
