#!/usr/bin/env python

import logging
logger = logging.getLogger("Services")

class Umodes(object):
	def __init__(self, plugin):
		self.plugin = plugin
		self.bot = self.plugin.bot

	def set_mode(self, modes):
		self.bot.ircsock.mode(self.bot.ircsock.getnick(), modes)
		logger.info("Setting umodes {0}".format(modes))

class NickServ(object):
	"""Class represents common commands from Nickserv using Anope"""
	def __init__(self, plugin):
		self.plugin = plugin
		self.bot = self.plugin.bot

	def register(self):
		pass

	def group(self):
		pass

	def glist(self):
		pass

	def identify(self, ns_password):
		self.send("identify {0}".format(ns_password))
		logger.info("Authenticating to NickServ")

	def access(self):
		pass

	def set(self):
		pass

	def drop(self):
		pass

	def recover(self):
		pass

	def release(self):
		pass

	def ghost(self, ns_password):
		self.send("ghost {0}".format(ns_password))

	def alist(self):
		pass

	def info(self):
		pass

	def logout(self):
		pass

	def status(self):
		pass

	def update(self):
		self.send("update")

	def send(self, message):
		self.bot.ircsock.say("NickServ", message)

class Plugin(object):
	def __init__(self, bot):
		self.bot = bot
		self.name = "services"
		self.priority = 0
		self.nickserv = NickServ(self)
		self.umodes = Umodes(self)

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("oper", None, _help="(str/None) The username to send with /OPER, default: None")
		self.bot.config.set_safe("oper.password", None, _help="(str/None) The password to use with /OPER, default: None")
		self.bot.config.set_safe("oper.modes", None, _help="(str/None) Extra modes to set when /OPER'ing, default: None")
		self.bot.config.set_safe("nickserv.password", None, _help="(str/None) The password to authenticate to NickServ with, default: None")
		return True

	def call(self, message):
		if message.command == "001": # We only want these called on connect
			if (self.bot.config.get("oper") != None) and (self.bot.config.get("oper.password") != None):
				self.bot.ircsock.oper(self.bot.config.get("oper"), self.bot.config.get("oper.password"))

				if self.bot.config.get("oper.modes") != None:
					self.umodes.set_mode(self.bot.config.get("oper.modes"))

			if self.bot.config.get("nickserv.password") != None:
				self.nickserv.identify(self.bot.config.get("nickserv.password"))

		# check for nickserv's "auth to this nick" message as well
		# on connect, if nick is unavailable, try and ghost it first (setting)
		# if nick is unavailable, have alt_nick setting (alt_nick_password setting?)
