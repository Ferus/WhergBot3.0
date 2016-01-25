#!/usr/bin/env python

class Channels(object):
	"""Container for channel objects"""
	def __init__(self, bot):
		self.bot = bot
		self.__channels = {} # name: channelobject

	def __contains__(self, name):
		return True if name in self.__channels else False

	def __len__(self):
		return len(self.__channels)

	def __getitem__(self, name):
		if self.__contains__(name):
			return self.__channels[name]
		raise KeyError("That channel does not exist!")

	def __iter__(self):
		return iter(self.__channels.items())

	def add_channel(self, channel):
		"""Adds a channel"""
		if self.__contains__(channel.name):
			raise Exception("That channel already exists.")
		self.__channels[channel.name] = channel

	def remove_channel(self, channel):
		"""Removes a channel"""
		if not self.__contains__(channel):
			raise KeyError("That channel does not exist.")
		del self.__channels[channel.name]

	def get_channel(self, channel, create=False):
		"""Takes a channels name"""
		if not self.__contains__(channel):
			if create:
				newchan = Channel(channel)
				self.add_channel(newchan)
			else:
				raise KeyError("That channel does not exist.")
		return self.__channels[channel]


class Channel(object):
	# TODO
	# topic, topic_created_*
	"""Holds all Channel level functions/properties
	Properties defined here:
		name                - The channels name
		created             - The creation date of the channel (Numeric 329)
		modes               - The channels modes
		users               - A dict of User objects and their oplevel for each user in the channel
		user_count          - The number of User's in the channel
		topic               - The channels topic
		topic_created_by    - The name of the last User who edited the topic
		topic_created_time  - The time the topic was created
		key                 - The channels key
	"""
	def __init__(self, name, key=None):
		self.name = name
		self.created = None
		self.modes = []
		self.users = {} # name: [object, oplevel]
		self.user_count = 0
		self.topic = None
		self.topic_created_by = None
		self.topic_created_time = None
		self.key = key

	def set_modes(self, mode):
		"""We expect modes to be a string, can be multiple modes"""
		for mode in list(mode):
			if mode not in self.modes and mode != "+":
				self.modes.append(mode)

	def remove_modes(self, mode):
		"""Same as above, but remove"""
		for mode in list(mode):
			if mode in self.modes and mode != "-":
				self.modes.remove(mode)

	def get_modes(self):
		return self.modes

	def add_user(self, user, oplevel=None):
		"""Adds a user object"""
		if user.nick in self.users.keys():
			raise Exception("That user is already listed")
		self.users[user.nick] = [user, oplevel]
		self.user_count += 1

	def remove_user(self, user):
		"""Removes a user object from a channel by username"""
		if user not in self.users.keys():
			raise KeyError("That user is not listed")
		del self.users[user]
		self.user_count -= 1

	def get_users(self):
		"""Returns the userlist by name"""
		return self.users.keys()

	def get_oplevel(self, user):
		"""Returns the oplevel of given user (by name) on channel"""
		if user not in self.users.keys():
			raise KeyError("That user does not exist")
		return self.users[user][1]

	def set_oplevel(self, user, oplevel):
		"""Sets the oplevel of given user (by name) on channel"""
		if user not in self.users.keys():
			raise KeyError("That user does not exist")
		self.users[user][1] = oplevel
