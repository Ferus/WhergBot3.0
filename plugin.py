import os
import imp
import glob
import logging

logger = logging.getLogger('Plugin')

class PluginError(Exception):
	"""Plugin Error"""
	pass


class BasicPlugin(object):
	"""A basic plugin shell."""
	def __init__(self, bot):
		self.bot = bot
		self.name = self.__name__
		self.priority = 50
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		return True

	def call(self, message):
		pass


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

	# TODO remove get debug func
	def get(self, name):
		return self.__plugins[name]

	def _load(self, instance, path, mname):
		"""
		Loads a plugin by path. `PluginError' will be raised when either:
			A module cannot be loaded due to syntax/runtime/etc
			The module does not contain a `Plugin' class
			The `Plugin' class does not contain a `name' or `priority' attribute
			The 'Plugin' class does not contain a `finish' or `call' method
			The 'hook' method fails to return `True'
		Returns the module name
		"""
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

	def load(self, paths):
		"""Loads all plugins in the plugin directory.
		Takes a list of shell globs
		Fails if the Plugin does not have a Plugin class or
		the Plugin class does not have a load_priority attribute
		Returns a list of names of plugins that were loaded
		"""
		to_load = []
		plugins = []
		for m in paths:
			for path in glob.glob(m):
				if not "__init__.py" in path:
					try:
						mname = os.path.splitext(os.path.split(path)[-1])[0]
						logger.info("[Bot {0}]: Attempting to load plugin {1}".format(self.bot.name, mname))
						module = imp.load_source(mname, path)

						if not hasattr(module, "Plugin"):
							raise PluginError("Plugin class for plugin {0} does not exist!".format(mname))

						instance = module.Plugin(self.bot)

						if not hasattr(instance, "load_priority"):
							raise PluginError("Plugin class for plugin {0} does not contain a load priority number!".format(mname))

						to_load.append([instance, instance.load_priority, mname, path])
					except PluginError as e:
						logger.exception("[Bot {0}]: Error loading plugin at path '{1}'".format(self.bot.name, path))

		to_load.sort(key=lambda x: x[1], reverse=False) # Lowest first

		for instance in to_load:
			try:
				plugin = self._load(instance[0], instance[2], instance[3])
				plugins.append(plugin)
			except PluginError as e:
				logger.exception("[Bot {0}]: Error loading plugin '{1}'".format(self.bot.name, instance[0].name))

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

