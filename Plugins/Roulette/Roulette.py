#!/usr/bin/env python3
# Russian Roulette plugin.

# Credits to Buggles, MaoZedongs, and xqks of
# irc.datnode.net for helping me create a list
# of guns and their chamber size. <3
# <&Eutectic> Ferus: make a random event where the person misses himself and randomly shoots somebody in the channel, preferably someone who was playing rulette

import random

from plugin import BasicPlugin


def windex(lst):
	# Stolen from http://code.activestate.com/recipes/117241/
	'''an attempt to make a random.choose() function that makes weighted choices
	accepts a list of tuples with the item and probability as a pair'''
	wtotal = sum([x[1] for x in lst])
	n = random.uniform(0, wtotal)
	for item, weight in lst:
		if n < weight:
			break
		n = n - weight
	return item


class Gun(object):
	def __init__(self, name, chambers, reason):
		self.name = name
		self.chambers = [False] * chambers
		self.reason = reason.format(gun=self.name)
		self.rounds = 0

	def __str__(self):
		return "A {0} with {1} 'chambers' is loaded with {2} rounds.".format(self.name, len(self.chambers), self.rounds)

	def __repr__(self):
		return "<Gun: {0}:{1}/{2}>".format(self.name, self.rounds, len(self.chambers))

	def load(self):
		for chamber in range(0, len(self.chambers)):
			if all(self.chambers):
				# Already full
				break
			if self.chambers[chamber]:
				# Pass a loaded chamber
				continue
			else:
				# Replace an empty chamber with a round
				self.chambers[chamber] = not self.chambers[chamber]
				self.rounds += 1
				break
		random.shuffle(self.chambers)

	def shoot(self):
		if self.chambers[0] == True:
			if windex([(True, .10), (False, .90)]):
				# 10% chance it's a dud
				self.rounds -= 1
				self.chambers[0] = False
				return (False, "You sigh once you realize the shot was a dud!")

			elif windex([(True, .05), (False, .95)]):
				# 5% chance it backfires
				self.rounds -= 1
				self.chambers[0] = False
				return (False, "The {0} backfired! Sadly, you're still alive, but have suffered disfiguring scars.".format(self.name))

			else:
				reason = self.reason + " \002({0}/{1})\002".format(self.rounds, len(self.chambers))
				return (True, reason)

		else:
			# No bullet
			return (False, "\002*\002click\002*\002")


class Plugin(BasicPlugin):
	"""Roulette Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "roulette"
		self.priority = 0
		self.load_priority = 10
		self.gun = None
		self.playing = False

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "Russian Roulette")
		self.bot.config.set_safe("plugins."+self.name+".enable_klines", True, "(bool) Enable klines instead of channel kicks. (Requires oper)")
		self.bot.config.set_safe("plugins."+self.name+".channels", [], "(list) List of channels to play on")
		self.bot.config.set_safe("plugins."+self.name+".guns"
			,[['Smith & Wesson', 6]
			,['Colt Anaconda', 6]
			,['Colt Python', 6]
			,['Magnum', 6]
			,['Reichsrevolver', 6]
			,['Smith & Wesson Centennial', 5]
			,['Smith & Wesson Ladysmith', 5]
			,['Walker Colt', 6]
			,['Desert Eagle', 7]
			,['92FS', 17]
			,['P99', 16]
			,['PPK', 7]
			,['Single Action Army', 6]
			,['M9 Rafica', 20]
			,['S&W .500', 5]
			,['Tokarev', 8]
			,['G18', 19]
			,['G17', 17]
			,['Taurus Raging Bull', 5]
			,['Portal Gun', 6]
			,['Star Wars Blaster Pistol', 8]
			]
			,"(list) List of guns to use"
		)
		self.bot.config.set_safe("plugins."+self.name+".reasons"
			,['Head blown off by a {gun}'
			,'Shot themself to death with a {gun}'
			,'Lodged lead in their greymatter with a {gun}'
			,'Blew their mind (literally) with a {gun}'
			,'Sprayed brain goop all over the walls with a {gun}'
			,'Took the easy way out with a {gun}'
			,'Got lit up by a {gun}'
			]
			,"(list) List of reasons to use"
		)
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]
		person = message.origin()[1:]
		if origin not in self.bot.config.get("plugins."+self.name+".channels") and origin.startswith("#"):
			return None

		if message.params[1] == self.bot.config.get("command_trigger")+"roulette":
			if not self.playing:
				self.playing = True
				g = random.choice(self.bot.config.get("plugins."+self.name+".guns"))
				r = random.choice(self.bot.config.get("plugins."+self.name+".reasons"))
				self.gun = Gun(name=g[0], chambers=g[1], reason=r)
				self.gun.load()
				self.bot.ircsock.say(origin, "Loaded a {0} with {1} chambers.".format(g[0], g[1]))

			# Trigger
			result = self.gun.shoot()
			if result[0]:
				if self.bot.config.get("plugins."+self.name+".enable_klines") and self.bot.is_oper:
					self.bot.ircsock.kill(person, result[1])
				else:
					self.bot.ircsock.banByMask(origin, message.prefix[1:])
					self.bot.ircsock.kick(origin, person, result[1])
				self.playing = False
				self.gun = None
			else:
				self.bot.ircsock.say(origin, result[1])
				self.gun.load()
				self.bot.ircsock.say(origin, "Loading another round...")


