#!/usr/bin/env python

"""
User accounts, provides logging into the bot.

Authmodes supported: hostmask, certfp

Permissions range from lowest (0) being owner to highest (100) being a normal user
User           = 100
Low (hostmask) = 50
High (certfp)  = 10
Owner          = 0

User.account = account.UserAccount()
config.permissions.$NICK = UserAccount().auth


"""

class AuthorityError(Exception):
	"""Authority Error"""
	pass

class UserAccount(object):
	def __init__(self, bot, user):
		self.bot = bot
		self.user = user

		if self.bot.config.get("permissions.user.{0}".format(self.user.nick.lower())):
			self.load()
		else:
			self.auth = {"level": 100
				,"hostmask": []
				,"certfp": []
				,"authenticated": False # logged in with @account login
				,"username": ""
				,"password": ""
			}
			self.bot.config.set_safe(
				"permissions.user.{0}".format(self.user.nick.lower())
				,self.auth
				,_help="Permission Information for user {0}".format(self.user.nick)
			)

	def load(self):
		self.auth = self.bot.config.get("permissions.user.{0}".format(self.user.nick.lower()))
		self.auth["authenticated"] = False

	def save(self):
		self.bot.config.set(
			"permissions.user.{0}".format(self.user.nick.lower())
			,self.auth
			,_help="Permission Information for user {0}".format(self.user.nick)
		)

	def has_hostmask(self, mask):
		if mask in self.auth["hostmask"]:
			return True
		else:
			return False

	def has_certfp(self, fp): #fp here should be self.user.ssl_certfp
		if fp in self.auth["certfp"]:
			return True
		else:
			return False

	def add_hostmask(self, mask):
		#check if has hostmask perm or owner
		if mask not in self.auth["hostmask"]:
			self.auth["hostmask"].append(mask)
			return True
		return False

	def del_hostmask(self, mask):
		#check if has hostmask perm or owner
		if mask in self.auth["hostmask"]:
			self.auth["hostmask"].remove(mask)
			return True
		return False

	def add_certfp(self, fp):
		#check if has certfp perm or owner
		if fp not in self.auth["certfp"]:
			self.auth["certfp"].append(fp)
			return True
		return False

	def del_certfp(self, fp):
		#check if has certfp perm or owner
		if fp in self.auth["certfp"]:
			self.auth["certfp"].remove(fp)
			return True
		return False

	def get_permission(self):
		return self.auth["level"]

	def set_permission(self, level):
		self.auth["level"] = level

	def is_authenticated(self):
		#check if user is password authenticated with the bot
		if self.auth.get("authenticated"):
			return True
		return False

	def set_authenticated(self):
		self.auth["authenticated"] = True

