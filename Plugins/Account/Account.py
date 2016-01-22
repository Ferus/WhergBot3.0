#!/usr/bin/env python3

import hashlib
import logging
logger = logging.getLogger("Account")

def create_hash(string):
	h = hashlib.sha512()
	h.update(string.encode("utf-8"))
	return h.hexdigest()

class Plugin(object):
	"""
	User Account Plugin
	Handles authentication and login to the bot

	Planned in Plugin:
		users should not be able to give higher perms than what they have
		users can give themselves access up to certfp by registering a password with the bot and providing certfp
		registering with the bot automatically adds the current host to permissions and changes level to 50
		adding certfp changes level to 10
	"""
	#TODO admin functions/bypasses
	#TODO lowercase names?

	def __init__(self, bot):
		self.bot = bot
		self.name = "account"
		self.priority = 0 # call() last
		self.load_priority = 0 # load first

	def add_admin(self):
		"""Add the admin account through the console"""
		pass

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe(self.name, None, _help="Handles user authentication to the bot")
		self.bot.config.set_safe("salt", "superSecretSaltString", _help="Salt to use when salting user passwords")
		return True

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		target = message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"account" and len(message.params) >= 3 :
			# @account
			if message.params[2] == "login":
				if len(message.params) == 5:
					# Get the user object
					user = self.bot.users.get_user(target)
					# Check if the user is already logged in
					if user.account.is_authenticated():
						self.bot.ircsock.say(origin, "[Account] You are already logged in!")
						return None
					if user.account.auth.get("username") != "" and user.account.auth.get("password") != "":
						passwd = create_hash(self.bot.config.get("salt")+message.params[4])
						if user.account.auth.get("username") == message.params[3] and \
							user.account.auth.get("password") == passwd:
							user.account.set_authenticated()
							self.bot.ircsock.say(origin, "[Account] login success! You are now logged in!")
						else:
							self.bot.ircsock.say(origin, "[Account] login failed! Check your username and password!")
					else:
						self.bot.ircsock.say(origin, "[Account] User account does not exist, try `account register`!")
				else:
					self.bot.ircsock.say(origin, "[Account] login takes 'username' and 'password' to log in")

			elif message.params[2] == "logout":
				user = self.bot.users.get_user(target)
				if user.account.is_authenticated():
					user.account.auth["authenticated"] = False
					self.bot.ircsock.say(origin, "[Account] logout success!")
				else:
					self.bot.ircsock.say(origin, "[Account] You are not logged in!")

			elif message.params[2] == "register":
				if len(message.params) == 5:
					# Get the user object
					user = self.bot.users.get_user(target)
					# Check for existing login info
					if user.account.auth.get("username") == "" and user.account.auth.get("password") == "":
						passwd = create_hash(self.bot.config.get("salt")+message.params[4])
						user.account.auth["username"] = message.params[3]
						user.account.auth["password"] = passwd
						#and the host too!
						host = "{0}!{1}@{2}".format(user.nick, user.ident, user.host)
						user.account.add_hostmask(host)

						self.bot.ircsock.say(origin, "[Account] Login information processed! To log into the bot use " \
							"`\002{0}account login [user] [pass]\002`".format(self.bot.config.get("command_trigger")))
						self.bot.ircsock.say(origin, "[Account] Your current hostmask ({0}) has been made the default, " \
							"if you wish to change or add more, use `account [add|delete] hostmask`".format(host))

						if user.account.get_permission() > 50:
							user.account.set_permission(50)
							self.bot.ircsock.say(origin, "[Account] Your access level is now \00250\002")

						user.account.save()

					else:
						self.bot.ircsock.say(origin, "[Account] An existing account already exists for you ({0})".format(user.account.auth.get("username")))
				else:
					self.bot.ircsock.say(origin, "[Account] register takes 'username' and 'password' to log in")


			elif message.params[2] == "add":
				if len(message.params) == 5:
					user = self.bot.users.get_user(target)
					if user.account.is_authenticated():
						#TODO check for proper hostmask/certfp
						if message.params[3] == "hostmask":
							user.account.add_hostmask(message.params[4])
							user.account.save()
							self.bot.ircsock.say(origin, "[Account] Your hostmask has been added successfully!")
						elif message.params[3] == "certfp":
							cert = message.params[4].replace(":", "")
							if user.ssl_certfp == cert:
								user.account.add_certfp(cert)
								self.bot.ircsock.say(origin, "[Account] Your certfp ({0}) has been added successfully!".format(cert))
								if user.account.get_permission() > 10:
									user.account.set_permission(10)
									self.bot.ircsock.say(origin, "[Account] Your access level is now \00210\002")

								user.account.save()
							else:
								self.bot.ircsock.say(origin, "[Account] You must be currently using your certfp to add it.")
					else:
						self.bot.ircsock.say(origin, "[Account] You must be authenticated to the bot to use `account add'")
				else:
					self.bot.ircsock.say(origin, "[Account] add takes either 'hostmask' or 'certfp' and the hostmask/certfp to add")

			elif message.params[2] == "delete":
				if len(message.params) == 5:
					user = self.bot.users.get_user(target)
					if user.account.is_authenticated():
						#TODO check for proper hostmask/certfp
						if message.params[3] == "hostmask":
							user.account.del_hostmask(message.params[4])
						elif message.params[3] == "certfp":
							user.account.del_certfp(message.params[4])
					else:
						self.bot.ircsock.say(origin, "[Account] You must be authenticated to the bot to use `account delete'")
				else:
					self.bot.ircsock.say(origin, "[Account] delete takes either 'hostmask' or 'certfp' and the hostmask/certfp to delete")





