#!/usr/bin/env python3

import re
import requests
from html import unescape

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Word Etymology Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "etymology"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Poll the internet for a words etymology")
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"etym" and len(message.params) > 2:
			etyms = self.getWordEtymology(message.params[2])
			for etym in etyms:
				self.bot.ircsock.say(origin, "\002[Etymology]\002 {0} - {1}".format(message.params[2], etym))


	def getWordEtymology(self, word):
		try:
			info = requests.get("http://www.etymonline.com/index.php?term={0}".format(word)).text
		except requests.HTTPError as e:
			return None
		info = re.sub("[\r\n\t]", "", info)
		try:
			info = re.findall(r"<dd class=\"highlight\">(.*?)<\/dd>", info)[0]
		except IndexError as e:
			return ["Word origin not found!"]

		spans = re.findall(r"<span .*?>(.*?)<\/span>", info)
		for span in spans:
			info = re.sub(r"<span .*?>{0}<\/span>".format(span), "\x02{0}\x02".format(span), info)

		links = re.findall(r"<a href=\".*?\" class=\".*?\">(.*?)</a>", info)
		for link in links:
			info = re.sub(r"<a href=\".*?\" class=\".*?\">{0}</a>".format(link), link, info)

		origins = []
		for h in re.split(r"<BR><BR>", info):
			if h != "":
				origins.append(unescape(h))
		return origins
