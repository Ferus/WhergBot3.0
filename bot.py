#!/usr/bin/env python3

""" Basic IRC bot connection/config classes
"""
import os
import sys
import logging

import imp
import glob
import time
import queue
import bisect
import threading

import blackbox
import yaml

logging.basicConfig(filename="bot.log", filemode='a', level=logging.INFO, \
  format="[%(levelname)s]: %(name)s - %(filename)s - %(funcName)s() at line %(lineno)d: %(message)s")

logger = logging.getLogger("Core")

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
Formatter = logging.Formatter("\033[31m[%(levelname)s]\033[0m: " \
  "%(name)s - %(filename)s - %(funcName)s() at line %(lineno)d: %(message)s")
ch.setFormatter(Formatter)
logger.addHandler(ch)

class NotImplementedError(Exception):
	"""Not Implemented"""
	pass


class PluginError(Exception):
	"""Plugin Error"""
	pass


class BotConfig(object):
	"""Returns an object with config settings
  Settings:

	enabled (bool)
		True if this connection is to be started
	nickname (str)
		IRC Nickname
	realname (str)
		IRC Realname
	ident (str)
		IRC Ident
	host (str)
		Address of the IRC server
	port (int)
		Port to connect to
	server_password (str/None)
		The password to send with /PASS, default None
	ssl (bool)
		True if using SSL to connect
	oper (str/None)
		If not none, the username to send with /OPER, default None
	oper_password (str/None)
		The password to use with /OPER, default None
	channels (list)
		A list of channels to join to after connecting
	"""

	def __init__(self, name, options):
		self._name = name
		self._options = options

	def set(self, option, value):
		"""Sets option to value."""
		self._options[option] = value
		logger.info("[Bot {0}]: Setting '{1}' changed to value '{2}'".format(self._name, option, value))

	def set_safe(self, option, value):
		"""If the option is already set, return false, else set the option and return true"""
		if (self.get(option) == None):
			self.set(option, value)
			return True
		return False

	def get(self, option, default=None):
		"""Returns the value for option given"""
		return self._options.get(option, default)

	def save(self):
		"""Writes changes to the config file"""
		logger.info("[Bot {0}]: Saving config file.".format(self._name))
		with open("config.yaml", "r") as _config:
			config = yaml.load(_config)
		logger.info("[Bot {0}]: Loaded old config.".format(self._name))

		for key, value in self._options.items():
			config[self._name][key] = value
		logger.info("[Bot {0}]: Copying new values.".format(self._name))

		with open("config.yaml", "w") as _config:
			yaml.dump(config, _config, canonical=True)
		logger.info("[Bot {0}]: Saved config file.".format(self._name))


class Bot(object):
	"""Bot object"""
	def __init__(self, name, config):
		self.name = name
		self.config = config # we can add more as we're running, plugins subconfig?
		self.plugins = PluginManager(self)
		self.onLoad = [] # list of functions to call after connecting to an IRC server.
		self.running = False
		self.parser = Parser(self)

	def init(self):
		"""Last minute configuration/setting up for running, loads plugins."""
		ssl = self.config.get("ssl", False)
		logger.info("[Bot {0}]: SSL set to {1}".format(self.name, ssl))
		oper = self.config.get("oper", None)
		if oper:
			logger.info("[Bot {0}]: Oper mode enabled.".format(self.name))
			self.ircsock = blackbox.Oper(ssl=ssl)
		else:
			self.ircsock = blackbox.IRC(ssl=ssl)

		self.plugins.load_glob(self.config.get("plugins"))

	def run(self):
		"""Calls ircsock.connect() and connects to the server
		Handles all onLoad functions"""

		try:
			host = self.config.get("host")
			port = self.config.get("port")
			self.ircsock.connect(host, port)
			logger.info("[Bot {0}] Initializing connection.".format(self.name))
		except Exception as e:
			logger.exception("[Bot {0}] Error connecting to server, waiting 15 seconds.".format(self.name))
			time.sleep(15)
			self.run()

		self.running = True

		nick = self.config.get("nickname")
		self.ircsock.nickname(nick)
		logger.info("[Bot {0}] Sending nickname.".format(self.name))

		self.parser.start()

		ident = self.config.get("ident")
		real = self.config.get("realname")
		self.ircsock.username(ident, real)
		logger.info("[Bot {0}] Sending Ident and Realname".format(self.name))

		while len(self.onLoad) > 0:
			try:
				self.onLoad.pop(0)()
			except Exception as e:
				logger.error("[Bot {0}] Error occured in an onLoad() function:".format(self.name))

	def quit(self, message="I am going to sleep~", reload=False):
		"""Quits the connection and cleans up, saves bot config."""
		for plugin in list(self.plugins):
			# plugin = (name, [instance, priority])
			self.plugins.unload(plugin[0])

		self.config.save()
		self.ircsock.quit(message)
		if not reload:
			self.running = False

	def reload(self):
		"""Reload a specific bot, this kills the current connection and restarts it"""
		self.quit(message="I am being reloaded, brb in 5 seconds!", reload=True)
		self.onLoad = []
		time.sleep(5)
		self.init()
		self.run()


class Parser(blackbox.parser.Parser):
	"""Handles all IRC messages"""
	def __init__(self, bot):
		self.bot = bot
		self.plugins = self.bot.plugins
		self.__queue = queue.Queue()

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
			while self.bot.running and self.bot.ircsock.isConnected():
				message = self.bot.ircsock.recv()
				self.put(message)
		_in = threading.Thread(target=helper)
		_in.daemon = True
		_in.start()

		def helper2():
			"""Helper function to run in a thread, parses new messages in queue"""
			while self.bot.running and self.bot.ircsock.isConnected():
				message = self.get()

				# Sort plugins based on priority
				plugins = []
				for x in list(self.bot.plugins):
					plugins.append(x[1])
				plugins.sort(key=lambda x: x[1], reverse=True)

				def sender():
					"""Helper function to handle sending plugins the message"""
					for plugin in plugins:
						plugin[0].call(message)
				senderThread = threading.Thread(target=sender)
				senderThread.daemon = True
				senderThread.start()
				senderThread.join()

		_out = threading.Thread(target=helper2)
		_out.daemon = True
		_out.start()


class PluginManager(object):
	"""Plugin Manager class, manages all plugins.
	"""
	def __init__(self, bot):
		self.__plugins = {} # name: [instance, priority]
		self.bot = bot

	def __contains__(self, name):
		return True if name in self.__plugins else False

	def __len__(self):
		return len(self.__plugins)

	def __getitem__(self, name):
		if self.__contains__(name):
			return self.__plugins[name]
		raise KeyError("That plugin does not exist!")

	def __iter__(self):
		return iter(self.__plugins.items())

	def load(self, path):
		"""Loads a plugin by path
		Raises PluginError when module cannot be loaded, does not contain a 'Plugin'
		class, 'Plugin' class does not contain a 'name' or 'priority' attribute,
		'Plugin' class does not contain a finish or call method, or the 'hook' method
		fails to return True
		Returns the module name
		"""
		mname = os.path.splitext(os.path.split(path)[-1])[0]
		logger.info("[Bot {0}] Attempting to load plugin {1}".format(self.bot.name, mname))
		module = imp.load_source(mname, path)


		if not hasattr(module, "Plugin"):
			raise PluginError("Plugin class for plugin {0} does not exist!".format(mname))

		instance = module.Plugin(self.bot)

		if not hasattr(instance, "name"):
			raise PluginError("Plugin class for plugin {0} does not contain a name!".format(mname))

		if not hasattr(instance, "priority"):
			raise PluginError("Plugin class for plugin {0} does not contain a priority number!".format(mname))

		if not hasattr(instance, "finish"):
			raise PluginError("Plugin class for plugin {0} does not contain a finish method!".format(mname))

		if not hasattr(instance, "call"):
			raise PluginError("Plugin class for plugin {0} does not contain a call method!".format(mname))

		if not instance.hook():
			raise PluginError("Plugin class for plugin {0} can not be hooked!".format(mname))

		self.__plugins[instance.name] = [instance, instance.priority]

		logger.info("[Bot {0}] Loaded plugin {1}".format(self.bot.name, mname))
		return mname

	def load_glob(self, paths):
		"""Loads all plugins in the plugin directory."""
		plugins = []
		for m in paths:
			for path in glob.glob(m):
				if not "__init__.py" in path:
					try:
						plugins.append(self.load(path))
					except PluginError as e:
						logger.exception("[Bot {0}] Error loading plugin at path '{1}'".format(self.bot.name, path))
		return plugins

	def unload(self, plugin):
		"""Unloads specified plugin by name"""
		if plugin not in self.__plugins:
			return False
		self.__plugins[plugin][0].finish()
		del self.__plugins[plugin]
		logger.info("[Bot {0}] Unloaded plugin {1}".format(self.bot.name, plugin))

	def reload(self, plugin):
		"""Unloads, and reloads a plugin by name"""
		# TODO figure out how to solve this
		if plugin not in self.__plugins:
			return False
		self.unload(plugin)
		#imp.reload(self.__plugins[plugin][0])

if __name__ == '__main__':
	bots = []
	with open("config.yaml", "r") as _config:
		configs = yaml.load(_config)
	for key, config in configs.items():
		if config.get("enabled"):
			logger.info("[Core]: Bot '{0}' is now being loaded!".format(key))
			configObj = BotConfig(key, config)
			bot = Bot(key, configObj)
			bots.append(bot)
	for bot in bots:
		logger.info("[Core]: Bot '{0}', calling init()!".format(bot.name))
		bot.init()
		logger.info("[Core]: Bot '{0}', calling run()!".format(bot.name))
		bot.run()

	# Check for dead bots, and quit when none are left
	while len(bots) > 0:
		for bot in bots:
			if not bot.running:
				bots.remove(bot)
				if len(bots) == 0:
					break
		time.sleep(20)
