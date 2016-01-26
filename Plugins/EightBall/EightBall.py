#!/usr/bin/env python3

from random import choice

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""8ball Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "eightball"
		self.priority = 0
		self.load_priority = 10

		self.replies = ["It is certain"
			,"It is decidedly so"
			,"Without a doubt"
			,"Yes - definitely"
			,"You may rely on it"
			,"As I see it yes"
			,"Most likely"
			,"Outlook good"
			,"Signs point to yes"
			,"Yes"
			,"Reply hazy try again"
			,"Ask again later"
			,"Better not tell you now"
			,"Cannot predict now"
			,"Concentrate and ask again"
			,"Don't count on it"
			,"My reply is no"
			,"My sources say no"
			,"Outlook not so good"
			,"Very doubtful"
			]

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Ask the magic 8ball a question and recieve an answer!")
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"8ball":
			self.bot.ircsock.say(origin, "{0}: {1}".format(message.origin()[1:], choice(self.replies)))

