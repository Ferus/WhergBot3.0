#!/usr/bin/env python3

import time

from plugin import BasicPlugin
from account import AuthorityError

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
		self.bot.config.set_safe("plugins."+self.name, False, _help="Supplies plugin @reload, @join, @part, and @quit")

		self.bot.config.set_safe("plugins."+self.name+".permission_levels.reload"
			,0
			,_help="(int) Required level to reload bot plugins"
		)
		self.bot.config.set_safe("plugins."+self.name+".permission_levels.join"
			,0
			,_help="(int) Required level to have bot join a channel"
		)
		self.bot.config.set_safe("plugins."+self.name+".permission_levels.part"
			,0
			,_help="(int) Required level to have bot part a channel"
		)
		self.bot.config.set_safe("plugins."+self.name+".permission_levels.quit"
			,0
			,_help="(int) Required level to have bot quit the server"
		)

		self.bot.config.set_safe("channels.autorejoin.on_kick"
			,False
			,_help="(bool) Whether to autorejoin a channel when kicked"
		)
		self.bot.config.set_safe("channels.autorejoin.delay"
			,15
			,_help="(int) How long to wait in seconds before rejoining, 0 to disable"
		)
		self.bot.config.set_safe("channels.autorejoin.harass"
			,False
			,_help="(bool) Whether to rejoin and kick the kicker (Requires Oper)"
		)
		self.bot.config.set_safe("channels.autorejoin.harass_message"
			,"Wow, that's pretty fucking rude mate!"
			,_help="(str) Kick message for autorejoin"
		)
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command == "001":
			self.bot.ircsock.join(",".join(self.bot.config.get('channels')))

		if message.command == "PRIVMSG":
			origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
			user = self.bot.users.get_user(message.origin()[1:])

			if message.params[1] == self.bot.config.get("command_trigger")+"reload" and len(message.params) == 3:
				if user.account.auth.get("level") > self.bot.config.get("plugins."+self.name+".permission_levels.reload") or \
					not user.account.auth.get("authenticated"):
					raise AuthorityError(self.bot, user.nick, "You do not have permission to access this command")

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

			elif message.params[1] == self.bot.config.get("command_trigger")+"join":
				if user.account.auth.get("level") > self.bot.config.get("plugins."+self.name+".permission_levels.join"):
					raise AuthorityError(self.bot, user.nick, "You do not have permission to access this command")

				if len(message.params) == 3:
					self.bot.ircsock.join(message.params[2])
				elif len(message.params) == 4:
					self.bot.ircsock.join(message.params[2], message.params[3])
				else:
						self.bot.ircsock.notice(origin, "Syntax is `@join channel[,channel] [key[,key]]'")

			elif message.params[1] == self.bot.config.get("command_trigger")+"part":
				if user.account.auth.get("level") > self.bot.config.get("plugins."+self.name+".permission_levels.part"):
					raise AuthorityError(self.bot, user.nick, "You do not have permission to access this command")
				if len(message.params) == 3:
					self.bot.ircsock.part(message.params[2])
				else:
					self.bot.ircsock.notice(origin, "Syntax is `@part channel[,channel]'")

			elif message.params[1] == self.bot.config.get("command_trigger")+"quit":
				if user.account.auth.get("level") > self.bot.config.get("plugins."+self.name+".permission_levels.quit"):
					raise AuthorityError(self.bot, user.nick, "You do not have permission to access this command")
				self.bot.quit(" ".join(message.params[2:])) if len(message.params) >= 3 else self.bot.quit()

		if message.command == "KICK":
			#['#h', 'WhergBotv3', 'Ferus']
			if self.bot.config.get("channels.autorejoin.on_kick"):
				delay = self.bot.config.get("channels.autorejoin.delay")
				if delay != 0:
					time.sleep(delay)
				self.bot.ircsock.join(message.params[0])

				if self.bot.config.get("channels.autorejoin.harass") and self.bot.is_oper:
					self.bot.ircsock.kick(message.params[0], message.origin()[1:], self.bot.config.get("channels.autorejoin.harass_message"))


# TODO
# add support for keys in @join and @part and autorejoin
# Get it from self.bot.channels.get_channel().key
