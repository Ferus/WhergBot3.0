import sqlite3

from account import UserAccount

class Users(object):
	"""Container for user objects"""
	def __init__(self, bot):
		self.bot = bot
		self.__users = {} # name: userobject

	def __contains__(self, name):
		name = name.lower()
		return True if name in self.__users else False

	def __len__(self):
		return len(self.__users)

	def __getitem__(self, name):
		name = name.lower()
		if self.__contains__(name):
			return self.__users[name]
		raise KeyError("That user does not exist!")

	def __iter__(self):
		return iter(self.__users.items())

	def add_user(self, user):
		"""Takes a user object"""
		if self.__contains__(user.nick.lower()):
			raise Exception("That user already exists.")
		self.__users[user.nick.lower()] = user

	def remove_user(self, user):
		"""Takes a user object"""
		if not self.__contains__(user.nick.lower()):
			raise KeyError("That user doesnt exist.")
		del self.__users[user.nick.lower()]

	def get_user(self, name, create=False, create_account=True):
		"""Takes a users name"""
		if not self.__contains__(name.lower()):
			if create:
				newuser = User(name.lower())
				if create_account:
					newuser.account = UserAccount(self.bot, newuser)
				self.add_user(newuser)
			else:
				raise KeyError("That user doesnt exist.")
		return self.__users[name.lower()]

class User(object):
	"""Holds all User level functions/User information
	Properties defined here:
		nick            - The users nick
		ident           - The users ident
		host            - The users host
		realname        - The users realname
		server          - Server the user is connected to
		server_info     - Info line for the server
		server_hops     - Number of hops away the user is
		authenticated   - Is the user authenticated to IRC Services (Anope)
		is_away         - Is the user /AWAY?
		is_oper         - Is the user an IRC Operator
		is_bot          - Is the user an IRC Bot (Umode +B)
		ssl             - Is the user using ssl
		ssl_certfp      - The clients certfp fingerprint, if available
		swhois          - The clients swhois, if available
		usermodes       - The users usermodes (Oper Only)
		channels        - List of known channels the user is a part of
		account         - The account object for the user (provides authentication)
	"""
	def __init__(self, nick):
		self.nick = nick
		self.ident = None
		self.host = None
		self.real = None
		self.server = None
		self.server_info = None
		self.server_hops = None
		self.authenticated = False
		self.is_away = False
		self.is_oper = False
		self.is_bot = False
		self.ssl = False
		self.ssl_certfp = None
		self.swhois = None
		self.usermodes = []
		self.channels = {} # name: [object, oplevel]
		self.account = None
		self.whois_update_level = 2
		self._first_whois = False

	# only opers can see usermodes
	def set_umodes(self, modes):
		"""We expect modes to be a string, can be multiple modes"""
		for mode in list(modes):
			if mode not in self.usermodes and mode != "+":
				self.usermodes.append(mode)

	def remove_umodes(self, modes):
		for mode in list(modes):
			if mode in self.usermodes and mode != "-":
				self.usermodes.remove(mode)

	def get_umodes(self):
		return self.usermodes

	def add_channel(self, channel, oplevel=None):
		"""Add a channel, by object"""
		if channel in self.channels:
			raise Exception("That channel is already listed")
		self.channels[channel.name] = [channel, oplevel]

	def remove_channel(self, channel):
		"""Remove a channel, by channel name"""
		if channel not in self.channels.keys():
			raise KeyError("That channel is not listed")
		del self.channels[channel]

	def get_channels(self):
		"""Returns a list of all the names of channels"""
		return list(self.channels.keys())

	def get_oplevel(self, channel):
		"""Returns a users oplevel for the given channel by name"""
		if channel not in self.channels.keys():
			raise KeyError("That channel does not exist")
		return self.channels[channel][1]

	def set_oplevel(self, channel, oplevel):
		"""Sets the oplevel (numeric) for user on given channel by name"""
		if channel not in self.channels.keys():
			raise KeyError("That channel does not exist")
		self.channels[channel][1] = oplevel
