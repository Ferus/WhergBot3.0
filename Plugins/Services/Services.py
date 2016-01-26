#!/usr/bin/env python

import logging
logger = logging.getLogger("Services")

from plugin import BasicPlugin

class Umodes(BasicPlugin):
	def __init__(self, plugin):
		self.plugin = plugin
		self.bot = self.plugin.bot

	def set_mode(self, modes):
		self.bot.ircsock.mode(self.bot.ircsock.getnick(), modes)
		logger.info("Setting umodes {0}".format(modes))

class NickServ(BasicPlugin):
	"""Class represents common commands from Nickserv using Anope"""
	def __init__(self, plugin):
		self.plugin = plugin
		self.bot = self.plugin.bot

	def register(self, ns_password, email=""):
		logger.info("Registering nickname{0}".format("" if email == "" else "to email account "+email))
		if email != "":
			self.send("REGISTER {0} {1}".format(ns_password, email))
		else:
			self.send("REGISTER {0}".format(ns_password))

	def group(self, target, ns_password):
		logger.info("Grouping to {0}'s account".format(target))
		self.send("GROUP {0} {1}".format(target, ns_password))

	def glist(self, target=""):
		# TODO Oper mode check + target
		logger.info("Requesting group listing")
		self.send("GLIST")

	def identify(self, ns_password, account=""):
		if account == "":
			logger.info("Authenticating to NickServ")
			self.send("IDENTIFY {0}".format(ns_password))
		else:
			logger.info("Authenticating to NickServ as {0}".format(account))
			self.send("IDENTIFY {0} {1}".format(account, ns_password))

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

class Plugin(BasicPlugin):
	def __init__(self, bot):
		self.bot = bot
		self.name = "services"
		self.priority = 0
		self.load_priority = 10
		self.nickserv = NickServ(self)
		self.umodes = Umodes(self)

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("oper", None, _help="(FalseNone) The username to send with /OPER")
		self.bot.config.set_safe("oper.password", None, _help="(str/None) The password to use with /OPER")
		self.bot.config.set_safe("oper.modes", None, _help="(str/None) Extra modes to set when /OPER'ing")
		self.bot.config.set_safe("nickserv.password", None, _help="(str/None) The password to authenticate to NickServ with")
		self.bot.config.set_safe("nickserv.nick_in_use", "alt_nick", _help="(str/None) What to do when username is in use, \x02alt_nick\x02 or \x02ghost\x02")
		self.bot.config.set_safe("nickname.alt", self.bot.config.get("nickname") + "-", _help="(str) Alternative nickname to use when main is taken")
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command == "001": # We only want these called on connect
			if self.bot.is_oper:
				self.bot.ircsock.oper(self.bot.config.get("oper"), self.bot.config.get("oper.password"))

				if self.bot.config.get("oper.modes") != None:
					self.umodes.set_mode(self.bot.config.get("oper.modes"))

			if self.bot.config.get("nickserv.password") != None:
				self.nickserv.identify(self.bot.config.get("nickserv.password"))

		if message.command == "433":
			if self.bot.config.get("nickserv.nick_in_use") == "alt_nick":
				logger.info("Nickname {0} already in use, trying setting nickname.alt ({1}) instead".format( \
					self.bot.config.get("nickname"), self.bot.config.get("nickname.alt")))
				self.bot.ircsock.nickname(self.bot.config.get("nickname.alt"))
			else:
				pass

		# check for nickserv's "auth to this nick" message as well
