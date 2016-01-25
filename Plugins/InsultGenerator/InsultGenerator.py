#!/usr/bin/env python3

import re
import requests

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Insult Generator"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "insult"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Polls insultgenerator.org for a random insult.")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None
		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		if message.params[1] == self.bot.config.get("command_trigger")+"insult" and len(message.params) > 2:
			self.bot.ircsock.say(origin, "{0}: {1}".format(" ".join(message.params[2:]), self.generateInsult()))

	def generateInsult(self):
			html = requests.get("http://insultgenerator.org/")
			if html.status_code == 200:
				insult = re.search(r'<div class="wrap">(?:<br><br>)?(.*?)</div>', html.text.replace("\n", "")).group(1)
				return insult
			else:
				return "There was an error connecting to InsultGenerator, faggot."

