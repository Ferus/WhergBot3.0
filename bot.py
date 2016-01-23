#!/usr/bin/env python3

"""
Basic IRC bot connection/config classes
"""

import sys
import time
import json
import logging

from blackbox import blackbox

from parser import Parser
from plugin import PluginManager
from user import User, Users
from channel import Channel, Channels

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

class BotConfig(object):
	"""Returns an object with config and help settings.
	When setting an option, you can specify a _help string
	"""

	def __init__(self, name, options):
		self._name = name
		self.__options = options

		# Insert defaults safely
		self.set_safe("enabled", True, _help="(bool) True if this connection is to be started")
		self.set_safe("nickname", "WhergBot", _help="(str) IRC Nickname to use")
		self.set_safe("realname", "WhergBot [3.0] Ferus", _help="(str) IRC Realname to use")
		self.set_safe("ident", "Wherg", _help="(str) IRC Ident to use")
		self.set_safe("host", "irc.datnode.net", _help="(str) Address of the IRC server to connect to")
		self.set_safe("port", 6667, _help="(int) Port of the IRC server to connect to")
		self.set_safe("channels", ["#hacking"], _help="(list) A list of channels to /JOIN on connect")
		self.set_safe("server_password", None, _help="(str/None) The password to send with /PASS")
		self.set_safe("ssl", False, _help="(bool) True if using SSL to connect")
		self.set_safe("reload.wait", 5, _help="(int) The number of seconds to wait when being reloaded")
		self.set_safe("command_trigger", "@", _help="(str) The character string used to trigger commands")

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
		if not self.__contains__(option):
			self.set(option, value, _help)
			return True
		return False

	def get(self, option, default=None):
		"""Returns the value for option given"""
		option = self.__options.get(option, default)
		return option[0] if isinstance(option, list) else default

	def get_help(self, option):
		"""Returns the help string for given option, or None if null or it doesnt exist"""
		__help = self.__options.get(option, None)
		return __help[1] if __help != None else "No help available."

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
		self.time = 0
		self.on_load = [] # list of functions to call after connecting to an IRC server.
		self.running = False
		self.is_oper = False
		self.plugins = PluginManager(self)
		self.parser = Parser(self)
		self.users = Users(self)
		self.channels = Channels(self)

	def init(self):
		"""Last minute configuration/setting up for running, loads plugins."""
		ssl = self.config.get("ssl", False)
		logger.info("[Bot {0}]: SSL set to {1}".format(self.name, ssl))
		if (self.config.get("oper", None) != None) and (self.config.get("oper.password", None) != None):
			logger.info("[Bot {0}]: Oper mode enabled.".format(self.name))
			self.is_oper = True # so we can find out we're an oper
			self.ircsock = blackbox.Oper(ssl=ssl)
		else:
			self.ircsock = blackbox.IRC(ssl=ssl)

		plugins = self.config.get("plugins")
		if plugins is not None:
			self.plugins.load(plugins)

	def run(self):
		"""Calls ircsock.connect() and connects to the server
		Handles all on_load functions"""

		try:
			host = self.config.get("host")
			port = self.config.get("port")
			self.ircsock.connect(host, port)
			logger.info("[Bot {0}]: Initializing connection.".format(self.name))
		except Exception as e:
			logger.exception("[Bot {0}]: Error connecting to server, waiting 15 seconds.".format(self.name))
			time.sleep(15)
			self.run()

		self.time = time.time()
		self.running = True

		nick = self.config.get("nickname")
		self.ircsock.nickname(nick)
		logger.info("[Bot {0}]: Sending nickname.".format(self.name))

		self.parser.start()

		ident = self.config.get("ident")
		real = self.config.get("realname")
		self.ircsock.username(ident, real)
		logger.info("[Bot {0}]: Sending Ident and Realname".format(self.name))

		while len(self.on_load) > 0:
			try:
				func = self.on_load.pop(0)
				func()
			except Exception as e:
				logger.error("[Bot {0}]: Error occured in an on_load() function: `{1}` from" \
					" plugin `{2}`".format(self.name, func.__name__, func.__module__))

	def on_connect(self, callback):
		"""Register a callback to be ran when connected"""
		self.on_load.append(callback)

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
		self.on_load = []
		time.sleep(self.config.get('reload.wait', 5))
		self.init()
		self.run()


if __name__ == '__main__':
	# Run enabled bots in config
	bots = []
	try:
		_config = open("config.json", "r")
	#This works in py3 and we're linting on py2
	#pylint: disable=E0602
	except (FileNotFoundError) as e:
		with open("config.json", "w") as _config:
			logger.warning("Config file does not exist! Creating it!")

	# TODO remove this config mess and see if botconfig init works
	try:
		with open("config.json", "r") as _config:
			configs = json.load(_config)
	except (ValueError) as e:
		_config = open("config.json", "w")
		logger.warning("Cannot load config, using defaults! " \
			"You may want to stop the bot and edit the config!")
		configs = {"default": {
				"enabled":
					[True, "(bool) True if this connection is to be started"],
				"nickname":
					["WhergBot_Default", "(str) IRC Nickname to use"],
				"realname":
					["WhergBot [3.0] Ferus", "(str) IRC Realname to use"],
				"ident":
					["Wherg", "(str) IRC Ident to use"],
				"host":
					["irc.datnode.net", "(str) Address of the IRC server to connect to"],
				"port":
					[6667, "(int) Port of the IRC server to connect to"],
				"channels":
					[["#hacking"], "(list) A list of channels to /JOIN on connect"],
				"server_password":
					[None, "(str/None) The password to send with /PASS"],
				"ssl":
					[False, "(bool) True if using SSL to connect"],
				"reload.wait":
					[5, "(int) The number of seconds to wait when being reloaded"],
				"plugins":
					[["Plugins/Services/Services.py"
					, "Plugins/General/General.py"
					, "Plugins/Exec/Exec.py"
					], "(list) A list of plugins to load"]
				}
			}
		json.dump(configs, _config, indent=4, separators=(',', ': '), sort_keys=True)
		_config.close()

	for key, config in configs.items():
		if config.get("enabled"):
			logger.info("[Bot {0}]: We are now being loaded!".format(key))
			configObj = BotConfig(key, config)
			bot = Bot(key, configObj)
			bots.append(bot)
	for bot in bots:
		logger.info("[Bot {0}]: Calling init()!".format(bot.name))
		bot.init()
		logger.info("[Bot {0}]: Calling run()!".format(bot.name))
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
