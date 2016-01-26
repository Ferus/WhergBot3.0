#!/usr/bin/env python3

import re
import requests
from random import choice

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Fuck My Life"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "fuckmylife"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Polls random FML's from FMyLife.com")
		self.fmlGenerator = self.fml()
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None
		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		if message.params[1] == self.bot.config.get("command_trigger")+"fml":
			self.bot.ircsock.say(origin, next(self.fmlGenerator))


	def get_fml(self):
		fml_db = []
		url = "http://fmylife.com/random"
		_html = requests.get(url)
		if _html.status_code != 200:
			return False #Error
		_html = _html.text #Page HTML
		comp = r'<div class="post article" id="[0-9]{1,}"><p><a href="\/[a-zA-Z0-9_-]{1,}\/[0-9]{1,}" class="fmllink">.*?</a></p>'
		tmp = re.findall(comp, _html)
		for x in tmp:
			x = re.sub(r'<div class="post article" id="[0-9]{1,}"><p><a href="\/[a-zA-Z0-9_-]{1,}\/[0-9]{1,}" class="fmllink">', "", x)
			x = re.sub(r'</a><a href="\/[a-zA-Z0-9_-]{1,}\/[0-9]{1,}" class="fmllink">', "", x)
			x = re.sub(r'</a></p>', "", x)
			fml_db.append(x)
		return fml_db

	def fml(self):
		fml_db = []
		while True:
			if not fml_db:
				print("* [FML] Getting more FML's.")
				fml_db = self.get_fml()
			_fml = fml_db.pop()
			yield "\x02[FML]\x02 {0}".format(_fml)

