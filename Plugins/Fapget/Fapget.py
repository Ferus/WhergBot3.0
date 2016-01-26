#!/usr/bin/env python3

import random
import logging
logger = logging.getLogger("Fapget")

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""Fapget Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "fapget"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def load_faps(self):
		try:
			with open("Plugins/Fapget/fapgets.txt", "r") as _fapgets:
				self.fapgets = _fapgets.readlines()
		except IOError:
			logger.exception("Reading fapgets.txt failed, does not exist?")
			return False
		return True

	def add_fap(self, fap):
		try:
			with open("Plugins/Fapget/fapgets.txt", "a") as _fapgets:
				_fapgets.write("{0}\n".format(fap))
			self.fapgets.append(fap)
			return True
		except IOError:
			logger.exception("Adding fapget to file failed.")
			return False

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Provides a random list of things for people to @fapget to")
		self.bot.config.set_safe("plugins."+self.name+".fap_allowed"
			,['Ferus!anonymous@the.interwebs']
			,_help="(list) A list of complete IRC hosts that are allowed to add faps"
		)
		return self.load_faps() and self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		target = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"fapget":
			fap = random.choice(self.fapgets).format(nick=message.origin()[1:])
			self.bot.ircsock.say(target, "{0} has to fap to: {1}".format(message.origin()[1:], fap))
			return None

		elif message.params[1] == self.bot.config.get("command_trigger")+"fapget.add":
			if message.prefix[1:] in self.bot.config.get("plugins."+self.name+".fap_allowed"):
				if len(message.params) >= 3:
					fap = " ".join(message.params[2:])
					if self.add_fap(fap):
						self.bot.ircsock.say(target, "Fap has been added successfully!")
					else:
						self.bot.ircsock.notice(target, "Error adding fap, check log for more info!")
				else:
					self.bot.ircsock.say(target, "No string supplied to add!")
			else:
				self.bot.ircsock.notice(target, "You are not allowed to add faps! :<")
			return None

#<+blam> ferus, for the new @fapget, add the current channel userlist to the list of things fapgettable ?
#<+blam> would need some way to update the userlist tho
#<+blam> maybe userlist plugin, and other plugins use that plugin?
# Core should handle channels and users in them, and should update the db on join/part/etc
# add some functions in core to make accessing this easy (self.bot.channels dict?) (could be a custom class)
