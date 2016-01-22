#!/usr/bin/env python3

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""General Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "general"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe(self.name, None, _help="Supplies plugin @reload, @join, @part, and @quit")
		self.bot.config.set_safe("permissions.denied", "You do not have permission to access this command"
			, _help="(str) Permission deny message for plugin @reload")
		self.bot.config.set_safe("permissions.owner", []
			, _help="(list) Holds a list of full IRC hostmasks (nick!ident@host) " \
			"of people who are allowed to use owner commands")
		self.bot.config.set_safe("permissions.reload", self.bot.config.get('permissions.owner', [])
			, _help="(list) Holds a list of full IRC hostmasks (nick!ident@host) " \
			"of people who are allowed to use the @reload command")
		return True

	def call(self, message):
		if message.command == "001":
			self.bot.ircsock.join(",".join(self.bot.config.get('channels')))

		if message.command == "PRIVMSG":
			origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

			if message.params[1] == self.bot.config.get("command_trigger")+"reload" and len(message.params) == 3:
				if message.prefix[1:] in self.bot.config.get("permissions.owner") or \
					message.prefix[1:] in self.bot.config.get("permissions.reload"):
					plugin = message.params[2]
					if plugin in self.bot.plugins:
						try:
							self.bot.plugins.reload(plugin)
							self.bot.ircsock.say(origin, "Reloaded `{0}' successfully!".format(plugin))
						except Exception as e:
							self.bot.ircsock.say(origin, "Error reloading `{0}' (see /NOTICE for details).".format(plugin))
							self.bot.ircsock.notice(origin, repr(e))
					else:
						self.bot.ircsock.say(origin, "That plugin does not exist!")
				else:
					self.bot.ircsock.notice(origin, self.bot.config.get("permissions.denied"))

			elif message.params[1] == self.bot.config.get("command_trigger")+"join":
				if len(message.params) == 3:
					self.bot.ircsock.join(message.params[2])
				elif len(message.params) == 4:
					self.bot.ircsock.join(message.params[2], message.params[3])
				else:
					self.bot.ircsock.notice(origin, "Syntax is `@join channel[,channel] [key[,key]]'")

			elif message.params[1] == self.bot.config.get("command_trigger")+"part":
				if len(message.params) == 3:
					self.bot.ircsock.part(message.params[2])
				else:
					self.bot.ircsock.notice(origin, "Syntax is `@part channel[,channel]'")

			elif message.params[1] == self.bot.config.get("command_trigger")+"quit":
				self.bot.quit(" ".join(message.params[2:])) if len(message.params) >= 3 else self.bot.quit()

# TODO
# add support for keys in @join and @part
