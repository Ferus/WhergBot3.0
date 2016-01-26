#!/usr/bin/env python3

import random

from plugin import BasicPlugin

class Plugin(BasicPlugin):
	"""WeedDice Plugin"""
	def __init__(self, bot):
		self.bot = bot
		self.name = "weeddice"
		self.priority = 0
		self.load_priority = 10

	def finish(self):
		pass

	def hook(self):
		self.bot.config.set_safe("plugins."+self.name, False, "WeedDice")
		self.bot.config.set_safe("plugins."+self.name+".dice"
			,{"1": ["You"
				, "Player of your choice"
				, "Player above you"
				, "Next player to send a message"
				, "Social (everyone)"
				, "Nobody"
				]
			, "2": ["take a puff"
				, "take 2 tokes"
				, "take a huge hit"
				, "take a tiny toke"
				, "finish a bowl"
				, "just chill"
				, "kill it with fire"
				]
			, "3": ["on your knees"
				, "while holding your nose"
				, "while typing"
				, "with your eyes closed"
				, "on one foot"
				, "while spinning in a circle"
				]
			, "4": ["then tell a joke"
				,"then post a song"
				,"then post a video"
				,"then type with your eyes closed"
				,"with the player below you"
				,"twice"
				]
			}
			,"WeedDice"
		)
		return self.bot.config.get("plugins."+self.name)

	def call(self, message):
		if message.command != "PRIVMSG":
			return None

		origin = message.params[0] if message.params[0] != self.bot.ircsock.getnick() else message.origin()[1:]

		if message.params[1] == self.bot.config.get("command_trigger")+"blaze":
			blaze = "\00303"
			config = self.bot.config.get("plugins."+self.name+".dice")
			for dice in range(1, 5):
				blaze += "[\002D{0}\002]{1}".format(str(dice), random.choice(config.get(str(dice))))
				blaze += " " if dice != 4 else ".\003"
			self.bot.ircsock.say(origin, blaze)
