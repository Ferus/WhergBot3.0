#!/usr/bin/env python3

class Plugin(object):
	"""General Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "general"
		self.priority = 0

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe(self.name, None, _help="Supplies plugin @reload, @join, @part, and @quit")
		self.bot.config.set_safe("reload.allowed", ["Ferus!anonymous@the.interwebs"]
			, _help="(list) Holds a list of full IRC hostmasks (nick!ident@host) " \
			"of people who are allowed to use the @reload command")
		self.bot.config.set_safe("permissions.denied", "You do not have permission to access this command"
			, _help="(str) Permission deny message for plugin @reload")
		return True

	def call(self, message):
		if message.command == "001":
			self.bot.ircsock.join(",".join(self.bot.config.get('channels')))

		if message.command == "PRIVMSG":
			if message.params[1] == "@reload" and len(message.params) == 3:
				if message.prefix[1:] in self.bot.config.get("reload.allowed"):
					plugin = message.params[2]
					if plugin in self.bot.plugins:
						try:
							self.bot.plugins.reload(plugin)
						except Exception as e:
							self.bot.ircsock.notice(message.origin()[1:], "Error reloading `{0}'".format(plugin))
							self.bot.ircsock.notice(message.origin()[1:], repr(e))
					else:
						self.bot.ircsock.notice(message.origin()[1:], "That plugin does not exist!")
				else:
					self.bot.ircsock.notice(message.origin()[1:], self.bot.config.get("permissions.denied"))

			elif message.params[1] == "@join":
				if len(message.params) == 3:
					self.bot.ircsock.join(message.params[2])
				elif len(params) == 4:
					self.bot.ircsock.join(message.params[2], message.params[3])
				else:
					self.bot.ircsock.notice(message.origin()[1:], "Syntax is `@join channel[,channel] [key[,key]]'")

			elif message.params[1] == "@part":
				if len(message.params) == 3:
					self.bot.ircsock.part(message.params[2])
				else:
					self.bot.ircsock.notice(message.origin()[1:], "Syntax is `@part channel[,channel]'")

			elif message.params[1] == "@quit":
				self.bot.quit(" ".join(message.params[2:])) if len(message.params) >= 3 else self.bot.quit()


