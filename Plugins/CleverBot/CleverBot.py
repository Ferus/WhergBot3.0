#!/usr/bin/env python3

from threading import Thread

from cleverbot import cleverbot
from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""CleverBot Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "cleverbot"
		self.priority = 0
		self.load_priority = 10
		self.instances = {} # k: channel v: cb.session()

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, None, "Talk with cleverbot!")
		self.bot.config.set_safe("plugins."+self.name+".channels", [], "(list) List of allowed channels")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		person = message.origin()[1:]
		instanceKey = "{0}.{1}".format(origin, person) if origin != person else origin

		if message.params[0] not in self.bot.config.get("plugins."+self.name+".channels") and\
			message.params[0].startswith("#"):
			return None

		#@cleverbot.start
		if message.params[1] == self.bot.config.get("command_trigger")+"cleverbot.start" and len(message.params) > 2:
			# Check if we're already initialized for the channel
			if instanceKey in self.instances.keys():
				# you cant start an already running instance
				self.bot.ircsock.say(origin, "\002[CleverBot]\002 There is already a cleverbot instance, try ending?")
				return None

			session = cleverbot.Session()
			self.instances[instanceKey] = session
			self.bot.ircsock.say(origin, "\002[CleverBot]\002 Connecting to Cleverbot.")
			reply = session.Ask(" ".join(message.params[2:]))
			self.bot.ircsock.say(origin, "\002[CleverBot]\002 CleverBot -> {0}: {1}".format(person, reply))

		#@cleverbot.reply
		if message.params[1] == self.bot.config.get("command_trigger")+"cleverbot.reply" and len(message.params) > 2:
			if instanceKey not in self.instances.keys():
				self.bot.ircsock.say(origin, "\002[CleverBot]\002 {0}: Not connected!".format(person))
				return None
			response = " ".join(message.params[2:])
			self.bot.ircsock.say(origin, "\002[CleverBot]\002 {0} -> CleverBot: {1}".format(person, response))
			session = self.instances[instanceKey]
			def helper(response):
				# Thread repliess.
				reply = session.Ask(response)
				self.bot.ircsock.say(origin, "\002[CleverBot]\002 CleverBot -> {0}: {1}".format(person, reply))

			t = Thread(target=helper, args=(response,))
			t.daemon = True
			t.start()


		#@cleverbot.end
		if message.params[1] == self.bot.config.get("command_trigger")+"cleverbot.end":
			if instanceKey not in self.instances.keys():
				return None
			session = self.instances[instanceKey]
			reply = session.Ask("Goodbye! :<")
			self.bot.ircsock.say(origin, "\002[CleverBot]\002 CleverBot -> {0}: {1}".format(person, reply))
			del self.instances[instanceKey]
