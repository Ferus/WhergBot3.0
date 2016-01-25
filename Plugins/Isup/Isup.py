#!/usr/bin/env python3

import re
import html
import requests

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Isup Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "isup"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Check if websites are up.")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"isup" and len(message.params) > 2:
			text = self.isup(message.params[2])
			if text:
				self.bot.ircsock.say(origin, "\002[ISUP]\002 {0}".format(text))
			else:
				self.bot.ircsock.say(origin, "I couldn't connect to http://isup.me/.")



	def isup(self, website):
		r = requests.get("http://isup.me/{0}".format(website))
		if r.status_code != 200:
			return None
		text = re.sub(r"\t|\n", "", r.text)
		text = re.findall(r"<div id=\"container\">(.*?)<p>.*?</div>", text)[0]
		text = re.sub(r"<a href=\".*?\" class=\"domain\">", "", text)
		text = re.sub(r"</a>(:?</span>)?", "", text)
		text = re.sub(r"\s{2,}", " ", text).strip(" ")
		text = html.unescape(text)
		return text
