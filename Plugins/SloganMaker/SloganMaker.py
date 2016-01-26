#!/usr/bin/env python3

import requests
import html

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""SloganMaker Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "sloganmaker"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Creates slogans!")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"slogan" and len(message.params) >= 3:
			self.bot.ircsock.say(origin, self.getSlogan(" ".join(message.params[2:])))

	def getSlogan(self, text):
		r = requests.post('http://www.sloganmaker.com/sloganmaker.php', data={'user':text})
		if r.status_code != 200:
			return "\x02[SloganMaker]\x02 Error; Status Code {0}".format(r.status_code)
		slogan = r.text.split('<p>')[1].split('</p>')[0]
		slogan = html.unescape(slogan)
		return "\x02[SloganMaker]\x02 {0}".format(slogan)
