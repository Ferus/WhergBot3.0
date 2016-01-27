#!/usr/bin/env python3

import re
import html
import sh
import requests
import logging

from plugin import BasicPlugin
from utils import truncate

logger = logging.getLogger("UrlAnnounce")
ip = sh.Command("/usr/bin/ip").bake("addr")

RE_TITLE = re.compile(r"<\s*title[^>]*>([^<]*)</title\s*>", re.IGNORECASE)

class Plugin(BasicPlugin):
	"""UrlAnnounce Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "urlannounce"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Announces url titles")
		self.bot.config.set_safe("plugins."+self.name+".url_regex", r"(https?|ftp):\/\/(([\w\-]+\.)+[a-zA-Z]{2,6}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?(\/([\w\-~.#\/?=&;:+%!*\[\]@$\'()+,|\^]+)?)?", "(str) the regex for matching url's")
		self.bot.config.set_safe("plugins."+self.name+".no_title", "No Title", "(str) The string shown when there is no title")
		self.bot.config.set_safe("plugins."+self.name+".blacklist"
			,["wikipedia.org"
			, "lmgtfy.com"
			, r"\.(?:mp4|wmv|flv|mp3|wav|flac|tar|tar\.*|tar\.gz|7z|\.r*|m4p|iso)$"
			]
			,"(list) list of hosts (regexs) to not fetch titles for"
		)
		self.ip = re.findall(r"inet .*\/24", str(ip()))[0].split()[1].split("/")[0]
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		for word in message.params[1:]:
			match = re.match(self.bot.config.get("plugins."+self.name+".url_regex"), word)
			if match:
				for blacklist in self.bot.config.get("plugins."+self.name+".blacklist"):
					if re.search(blacklist, word):
						logger.warn("Hit blacklisted site...")
						return None
				try:
					title = self.getTitle(word)
				except (requests.HTTPError, requests.ConnectionError) as e:
					logger.exception(e)
					return None
				except (requests.TooManyRedirects):
					title = "[too many redirects]"
				if not title:
					logger.warn("No title...")
					return None
				if self.ip:
					if re.search(re.escape(self.ip), title):
						title = "127.0.0.1"
				self.bot.ircsock.say(origin, "Title: '{0}' (at {1})".format(title, match.group(2)))

	def getTitle(self, url):
		# http://irc-bot-science.clsr.net/long (See ideas.txt)
		# http://irc-bot-science.clsr.net/internet.gz

		r = requests.get(url)
		r.raise_for_status()
		if "text" not in r.headers['content-type']:
			return None

		h = r.text
		title = RE_TITLE.search(h)
		if title:
			title = re.sub("[\r|\n|\t]+", "", title.group(1))
			title = html.unescape(title)
			title = truncate(title)
			return title
		return self.bot.config.get("plugins."+self.name+".no_title")


