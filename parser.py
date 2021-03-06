#!/usr/bin/env python

import re
import queue
import logging
import threading

from blackbox import blackbox

from user import Users, User
from channel import Channels, Channel
from account import UserAccount, AuthorityError

logger = logging.getLogger('Parser')

#pylint: disable=W0212,R0914

class Parser(blackbox.parser.Parser):
	"""Handles all IRC messages"""
	def __init__(self, bot):
		self.bot = bot
		self.plugins = self.bot.plugins
		self.__queue = queue.Queue()
		self.whois_levels = {
			"PRIVMSG": 1
			,"JOIN": 2
			,"PART": 3
		}

	def put(self, message):
		"""Puts a new message in queue"""
		self.__queue.put(message)

	def get(self):
		"""Returns a message from the queue"""
		return self.parse(self.__queue.get())

	def start(self):
		"""Starts the parser"""
		def helper():
			"""Helper function to run in a thread, gets new messages from IRC"""
			try:
				while (self.bot.running and self.bot.ircsock.isConnected()):
					message = self.bot.ircsock.recv()
					self.put(message)
			except (blackbox.IRCError) as e:
				logger.exception("[Bot {0}]: Connection Error:".format(self.bot.name))
		_in = threading.Thread(target=helper)
		_in.daemon = True
		_in.start()

		def helper2():
			"""Helper function to run in a thread, parses new messages in queue"""
			while self.bot.running and self.bot.ircsock.isConnected():
				message = self.get()

				# /WHO reply
				# :hub.datnode.net 352 WhergBotv3 #h anonymous the.interwebs areskeia.datnode.net Ferus Hr* 0 ferus
				# ['WhergBotv3', '#h', 'anonymous', 'the.interwebs', 'areskeia.datnode.net', 'Ferus', 'Hr*', '0', 'ferus']
				# params[6] H == avail; G == away; * == oper, r == registered nickserv
				if message.command == "352":
					nick = message.params[5]
					user = self.bot.users.get_user(nick, create=True)
					user.ident = message.params[2]
					user.host = message.params[3]
					user.server = message.params[4]
					user.authenticated = True if "r" in message.params[6] else False
					user.is_away = True if "G" in message.params[6] else False
					user.is_oper = True if "*" in message.params[6] else False
					user.is_bot = True if "B" in message.params[6] else False
					user.server_hops = message.params[7]
					user.real = " ".join(message.params[8:])
					user.account = UserAccount(self.bot, user)


				# /NAMES reply
				# parse namelist and create objects, add to self.bot.users
				if message.command == "353":
					names = message.params[3:]
					for name in names:
						if name == "":
							continue
						name = re.split("([+%@&~])", name) # TODO change this once 005 parsing (SUPPORT) is finished

						if len(name) == 3:
							oplevel = name[1]
							name = name[2]
						elif len(name) == 1:
							name = name[0]
							oplevel = None

						user = self.bot.users.get_user(name, create=True)

						channel = self.bot.channels.get_channel(message.params[2], create=True)
						if user.nick not in channel.get_users():
							channel.add_user(user, oplevel)

#				# Whois users when they are set to be re-whois'd
#				# Default is on /JOIN
#				if message.command in self.whois_levels:
#					name = message.origin()[1:]
#					user = self.bot.users.get_user(name)
#					if user.whois_update_level == self.whois_levels[message.command]:
#						user._first_whois = True
#						self.bot.ircsock.whois(name)
#
				# Generate User/Channel objects on JOIN
				if message.command == "JOIN":
					name = message.origin()[1:]

					# Send /MODE to get channel modes/create time (only when we join)
					if name == self.bot.ircsock.getnick():
						self.bot.ircsock.who(message.params[0])
						self.bot.ircsock.mode(message.params[0])
						channel = self.bot.channels.get_channel(message.params[0], create=True)

					else:
						user = self.bot.users.get_user(name, create=True)
						channel = self.bot.channels.get_channel(message.params[0])
						if user.nick not in channel.get_users():
							channel.add_user(user)
						if channel.name not in user.get_channels():
							user.add_channel(channel)

				if message.command == "PART":
					name = message.origin()[1:]
					chan = message.params[0]
					if name != self.bot.ircsock.getnick():
						user = self.bot.users.get_user(name)
						user.remove_channel(chan)
						channel = self.bot.channels.get_channel(chan)
						channel.remove_user(name)

				if message.command == "QUIT":
					name = message.origin()[1:]
					if name != self.bot.ircsock.getnick():
						user = self.bot.users.get_user(name)
						channels = user.get_channels()
						for channel in channels:
							# Remove channels from user object
							user.remove_channel(channel)
							# Remove user from each channel object
							channel = self.bot.channels.get_channel(channel)
							channel.remove_user(name)

				if message.command == "NICK":
					oldnick = message.origin()[1:]
					newnick = message.params[0]

					# remove the old one
					for channel in self.bot.users.get_user(oldnick).get_channels():
						self.bot.channels.get_channel(channel).remove_user(oldnick)
						self.bot.channels.get_channel(channel).add_user(newnick)
					self.bot.users.remove_user(oldnick)

					user = self.bot.users.get_user(newnick, create=True)

#					if oldnick != self.bot.ircsock.getnick():
#						# Not us


				# We want to /WHOIS new people when they first speak
				if message.command == "PRIVMSG":
					name = message.origin()[1:]
					user = self.bot.users.get_user(name)
					if user._first_whois == False:
						user._first_whois = True
						self.bot.ircsock.whois(name)

				if message.command == "MODE":
					# TODO parse modes
#					print(message.params)
					pass

				### START /WHOIS BLOCK
				#:apistia.datnode.net 311 WhergBot2 Ferus anonymous the.interwebs * h
				#311: "<nick> <user> <host> * :<real name>"
				if message.command == "311":
					#['WhergBot2', 'Ferus', 'anonymous', 'the.interwebs', '*', 'h']
					nick = message.params[1]
					user = self.bot.users.get_user(nick, create=True)
					user.ident = message.params[2]
					user.host = message.params[3]
					user.realname = message.params[5]

				#:apistia.datnode.net 307 WhergBot2 Ferus is a registered nick
				#307: registered to nickserv
				if message.command == "307":
					user = self.bot.users.get_user(nick)
					user.authenticated = True

				#:apistia.datnode.net 319 WhergBot2 Ferus ~#bots +#4chon &#hacking
				#319: List of channels
				if message.command == "319":
					nick = message.params[1]
					user = self.bot.users.get_user(nick)
					for channels in message.params[2].strip(" ").split(" "):
						channel = re.split("([+%@&~]?)", channels) # TODO change this once 005 parsing (SUPPORT) is finished
						if len(channel) == 3:
							oplevel = channel[1]
							channel = channel[2]
						elif len(channel) == 1:
							channel = channel[0]
							oplevel = None

						chan = self.bot.channels.get_channel(channel, create=True)
						if user.nick not in chan.get_users():
							chan.add_user(user, oplevel)
						if chan.name not in user.get_channels():
							user.add_channel(chan, oplevel)

				#:apistia.datnode.net 312 WhergBot2 Ferus areskeia.datnode.net The Complacent Man
				#312: "<nick> <server> :<server info>"
				if message.command == "312":
					nick = message.params[1]
					user = self.bot.users.get_user(nick)
					user.server = message.params[2]
					user.server_info = message.params[3]

				#:apistia.datnode.net 313 WhergBot2 Ferus is a Network Administrator
				#:apistia.datnode.net 313 WhergBot2 Boris is a Network Service
				if message.command == "313":
					nick = message.params[1]
					user = self.bot.users.get_user(nick)
					user.is_oper = True
					if message.params[2].endswith("Service"):
						user.authenticated = True

				#:apistia.datnode.net 335 WhergBot2 Ferus is a Bot on DatNode
				#335: user has +B set
				if message.command == "335":
					nick = message.params[1]
					user = self.bot.users.get_user(nick)
					user.set_umodes("B")
					user.is_bot = True

				#:apistia.datnode.net 671 WhergBot2 Ferus is using a Secure Connection
				#671: user is using ssl
				if message.command == "671":
					nick = message.params[1]
					user = self.bot.users.get_user(nick)
					user.ssl = True

				#:hub.datnode.net 276 WhergBotv3 Ferus has client certificate fingerprint e486ca3a446840367787fd13c0b9da8b970892f97303975de85e5f7bb068655a
				#276: user is using ssl certfp
				if message.command == "276":
					nick = message.params[1]
					user = self.bot.users.get_user(nick)
					user.ssl_certfp = message.params[-1]

				#:hub.datnode.net 320 WhergBotv3 Ferus [is] [a] [l33t] [h4x0r]
				#320: swhois
				if message.command == "320":
					nick = message.params[1]
					user = self.bot.users.get_user(nick)
					user.swhois = " ".join(message.params[2:])

				#:hub.datnode.net 330 WhergBotv3 Ferus Ferus is logged in as
				#330: nickserv accounts?
				# TODO implement and figure out what is missing?

				### END /WHOIS BLOCK

				#:aponoia.datnode.net 324 WhergBot2 #bots +ntr
				#['WhergBot2', '#bots', '+ntr', '']
				# .modes
				if message.command == "324":
					channel = self.bot.channels.get_channel(message.params[1], create=True)
					channel.set_modes(message.params[2].replace("+", ""))

				#:aponoia.datnode.net 329 WhergBot2 #bots 1383608565
				#['WhergBot2', '#bots', '1383608565']
				# .created
				if message.command == "329":
					channel = self.bot.channels.get_channel(message.params[1], create=True)
					channel.created = message.params[2]

				#:aponoia.datnode.net 332 WhergBot2 #bots Welcome to #bots, the future home of Skynet!
				# .topic
				if message.command == "332":
					channel = self.bot.channels.get_channel(message.params[1], create=True)
					channel.topic = " ".join(message.params[2:])

				#:aponoia.datnode.net 333 WhergBot2 #bots horkx3 1312180625
				# .topic_created_by
				# .topic_created_time
				if message.command == "333":
					channel = self.bot.channels.get_channel(message.params[1], create=True)
					channel.topic_created_by = message.params[2]
					channel.topic_created_time = message.params[3]

				# Sort plugins based on priority
				plugins = []
				for x in list(self.bot.plugins):
					plugins.append(x[1])
				plugins.sort(key=lambda x: x[1], reverse=True)

				def sender():
					"""Helper function to handle sending plugins the message"""
					for plugin in plugins:
						try:
							plugin[0].call(message)
						except AuthorityError as e:
							log = logging.getLogger("Account")
							log.warn("User {0} has no access to command!".format(e.user.nick))
							if self.bot.config.get("plugins.account.warn_user_on_autherror", False):
								self.bot.ircsock.notice(e.user.nick, e.message)
						except Exception as e:
							logger.exception(repr(e))

				senderThread = threading.Thread(target=sender)
				senderThread.daemon = True
				senderThread.start()
				senderThread.join()

		_out = threading.Thread(target=helper2)
		_out.daemon = True
		_out.start()
