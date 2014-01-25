#!/usr/bin/env python3

"""
Basic IRC bot connection/config classes
"""
import os
import sys
import logging

import imp
import glob
import time
import queue
import threading

from blackbox import blackbox
import json

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
	"""Returns an object with config and help settings.
	When setting an option, you can specify a _help string
	"""

	def __init__(self, name, options):
		self._name = name
		self.__options = options

		# insert defaults safely
		self.set_safe("enabled", False, _help="(bool) True if this connection is to be started")
		self.set_safe("nickname", "WhergBot", _help="(str) IRC Nickname to use")
		self.set_safe("realname", "WhergBot [3.0] Ferus", _help="(str) IRC Realname to use")
		self.set_safe("ident", "Wherg", _help="(str) IRC Ident to use")
		self.set_safe("host", "irc.datnode.net", _help="(str) Address of the IRC server to connect to")
		self.set_safe("port", 6667, _help="(int) Port of the IRC server to connect to")
		self.set_safe("server_password", None, _help="(str/None) The password to send with /PASS, default: None")
		self.set_safe("ssl", False, _help="(bool) True if using SSL to connect")
		self.set_safe("oper", None, _help="(str/None) The username to send with /OPER, default: None")
		self.set_safe("oper_password", None, _help="(str/None) The password to use with /OPER, default: None")
		self.set_safe("reload.wait", 5, _help="(int) The number of seconds to wait when being reloaded")

	def __contains__(self, name):
		return True if name in self.__options else False

	def __len__(self):
		return len(self.__options)

	def __getitem__(self, name):
		if self.__contains__(name):
			return self.__options[name]
		raise KeyError("That option does not exist!")

	def __iter__(self):
		return iter(self.__options.items())

	def set(self, option, value, _help=None):
		"""Sets option to value."""
		self.__options[option] = [value, _help]
		logger.info("[Bot {0}]: Setting '{1}' changed to value '{2}'".format(self._name, option, value))

	def set_safe(self, option, value, _help=None):
		"""If the option is already set, return false, else set the option and return true"""
		if (self.get(option) == None):
			self.set(option, value, _help)
			return True
		return False

	def get(self, option, default=None):
		"""Returns the value for option given"""
		option = self.__options.get(option, default)
		return option[0] if option != None else None

	def get_help(self, option):
		"""Returns the help string for given option, or None if null or it doesnt exist"""
		return self.__options.get(option, None)

	def save(self):
		"""Writes changes to the config file"""
		logger.info("[Bot {0}]: Saving config file.".format(self._name))
		with open("config.json", "r") as _config:
			config = json.load(_config)
		logger.info("[Bot {0}]: Loaded old config.".format(self._name))

		for key, value in self.__options.items():
			config[self._name][key] = value
		logger.info("[Bot {0}]: Copying new values.".format(self._name))

		with open("config.json", "w") as _config:
			json.dump(config, _config, indent=4, separators=(',', ': '), sort_keys=True)
		logger.info("[Bot {0}]: Saved config file.".format(self._name))


class Bot(object):
	"""Bot object"""
	def __init__(self, name, config):
		self.name = name
		self.config = config
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
			logger.info("[Bot {0}]: Initializing connection.".format(self.name))
		except Exception as e:
			logger.exception("[Bot {0}]: Error connecting to server, waiting 15 seconds.".format(self.name))
			time.sleep(15)
			self.run()

		self.running = True

		nick = self.config.get("nickname")
		self.ircsock.nickname(nick)
		logger.info("[Bot {0}]: Sending nickname.".format(self.name))

		self.parser.start()

		ident = self.config.get("ident")
		real = self.config.get("realname")
		self.ircsock.username(ident, real)
		logger.info("[Bot {0}]: Sending Ident and Realname".format(self.name))

		while len(self.onLoad) > 0:
			try:
				self.onLoad.pop(0)()
			except Exception as e:
				logger.error("[Bot {0}]: Error occured in an onLoad() function:".format(self.name))

	def quit(self, message="I am going to sleep~", reload=False):
		"""Quits the connection and cleans up, saves bot config."""
		for plugin in [_plugin[0] for _plugin in list(self.plugins)]:
			# plugin = (name, [instance, priority])
			self.plugins.unload(plugin)

		self.config.save()
		self.ircsock.quit(message)
		if not reload:
			self.running = False

	def reload(self):
		"""Reload a specific bot, this kills the current connection and restarts it"""
		self.quit(message="I am being reloaded, brb in {0} seconds!".format(self.config.get('reload.wait', 5)), reload=True)
		self.onLoad = []
		time.sleep(self.config.get('reload.wait', 5))
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
			try:
				while self.bot.running and self.bot.ircsock.isConnected():
					message = self.bot.ircsock.recv()
					self.put(message)
			except (blackbox.IRCError()) as e:
				logger.exception("[Bot {0}]: Connection Error:".format(self.bot.name))
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
		self.__plugins = {} # name: [instance, priority, path]
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
		"""
		Loads a plugin by path. `PluginError' will be raised when either:
			A module cannot be loaded due to syntax/runtime/etc
			The module does not contain a `Plugin' class
			The `Plugin' class does not contain a `name' or `priority' attribute
			The 'Plugin' class does not contain a `finish' or `call' method
			The 'hook' method fails to return `True'
		Returns the module name
		"""
		mname = os.path.splitext(os.path.split(path)[-1])[0]
		logger.info("[Bot {0}]: Attempting to load plugin {1}".format(self.bot.name, mname))
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

		self.__plugins[instance.name] = [instance, instance.priority, path]

		logger.info("[Bot {0}]: Loaded plugin {1}".format(self.bot.name, instance.name))
		return instance.name

	def load_glob(self, paths):
		"""Loads all plugins in the plugin directory."""
		plugins = []
		for m in paths:
			for path in glob.glob(m):
				if not "__init__.py" in path:
					try:
						plugins.append(self.load(path))
					except PluginError as e:
						logger.exception("[Bot {0}]: Error loading plugin at path '{1}'".format(self.bot.name, path))
		return plugins

	def unload(self, plugin):
		"""Unloads specified plugin by identifier"""
		if plugin not in self.__plugins:
			return False
		self.__plugins[plugin][0].finish()
		del self.__plugins[plugin]
		logger.info("[Bot {0}]: Unloaded plugin {1}".format(self.bot.name, plugin))

	def reload(self, plugin):
		"""Unloads, and reloads a plugin by name"""
		if plugin not in self.__plugins:
			return False
		path = self.__plugins[plugin][2]
		self.unload(plugin)
		self.load(path)

if __name__ == '__main__':
	# Run enabled bots in config
	bots = []
	with open("config.json", "r") as _config:
		configs = json.load(_config)
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
	# Graceful exit on ^C
	try:
		while len(bots) > 0:
			bots = [bot for bot in bots if bot.running]
			if len(bots) == 0:
				break
			time.sleep(20)
	except KeyboardInterrupt:
		print()
		for bot in bots:
			bot.quit()
	finally:
		sys.exit()
