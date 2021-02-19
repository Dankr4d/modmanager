# vim: ts=4 sw=4 noexpandtab

# TODO: Set rules ini init via sv.welcomeMessage if possible

import bf2
import host
import mm_utils

import random


# Set the version of your module here
__version__ = 1.0

# Set the required module versions here
__required_modules__ = {
	'modmanager': 1.6
}

# Does this module support reload ( are all its reference closed on shutdown? )
__supports_reload__ = True

# Sets which games this module supports
__supported_games__ = {
	'bf2': True,
	'bf2142': True
}

# Set the description of your module here
__description__ = "Rules v%s" % __version__

# Add all your configuration options here
configDefaults = {
	"showBold": 1,
	"showOrange": 1,
	"showEachSeconds": 5,
	"showOrdered": 1,
	"rulePrefix": "Rule (%number%): ",
	"ruleWarnNewlines": 13, # Newlines are added on warning
	"showRuleWarnBlur": 1, # Trigger blur effect when user is found
	"replaceWelcomeMessageWithRules": 1, # Will replace the welcome messages with the rules
	"rules": [
		"No teamkilling",
		"No highroofing",
		"No glitching",
		"No baserape",
		"No fighting commander",
		"No bad language",
		"No pod surfing",
		"No mines on titan shield",
		"No spotting in titan guns when shields are down",
	],
}

class Rules( object ):

	def __init__( self, modManager ):
		# ModManager reference
		self.mm = modManager

		# Internal shutdown state
		self.__state = 0

		# Const messages
		self.LESS_THAN_2_PARAMS = "You passed '%i' parameter but, required are at least 2."

		# Add any static initialisation here. TODO TODO TODO
		# Note: Handler registration should not be done here
		# but instead in the init() method

		# Your rcon commands go here:
		self.__cmds = {
			'warn': { 'method': self.cmdWarnRule, 'aliases': [ 'w' ], 'args': "<player|string> <ruleKeyWords|text>", 'level': 10 },
		}

		self.showRuleIdx = 0

	def announce(self, data):
		idx = 0

		if self.__showOrdered:
			idx = self.showRuleIdx
			self.showRuleIdx += 1
			if self.showRuleIdx == len(self.__rules):
				self.showRuleIdx = 0
		else:
			while True:
				# Prevent showing the last shown rule again
				idx = random.choice(range(len(self.__rules)))
				if idx != self.showRuleIdx:
					break
			self.showRuleIdx = idx

		rule = self.__rules[idx]

		if len(self.__rulePrefix) > 0:
			rule = self.__rulePrefix.replace('%number%', str(idx + 1)) + rule

		if self.__showBold:
			rule = "§2" + rule

		if self.__showOrange:
			rule = "|c1234" + rule

		mm_utils.msg_server(rule)


	def warnPlayer(self, playerName, text, playerId = -1):
		msg = ("\n" * self.__ruleWarnNewlines) + playerName + ": " + text
		# TODO: Add timer for duration. Currently message is shown ~4 seconds
		host.sgl_sendTextMessage(0, 12, 4, msg, 0)
		if self.__showRuleWarnBlur and playerId > -1:
			host.sgl_sendGameLogicEvent(playerId, 13, 1)


	def cmdExec( self, ctx, cmd ):
		"""Execute a MyModule sub command.""" # TODO: Replace this if we only have the warn sub command

		# Note: The Python doc above is used for help / description
		# messages in rcon if not overriden
		return mm_utils.exec_subcmd( self.mm, self.__cmds, ctx, cmd )


	def cmdWarnRule( self, ctx, cmd ):
		"""Warns a user for breaking a rule"""

		cmdSplit = cmd.split()
		cmdSplitLen = len(cmdSplit)

		if cmdSplitLen < 2:
			ctx.write(self.LESS_THAN_2_PARAMS % cmdSplitLen)
			return 0

		playerIdx = -1
		playerName = cmdSplit[0]
		ruleKeyWords = cmdSplit[1:]

		# Searching for complete player name
		# If not found, the inserted name by rcon admin is used
		for player in bf2.playerManager.getPlayers():
			if playerName.lower() in player.getName().lower():
				playerIdx = player.index
				# If no clantag is set there's a leading whitespace, that's why we strip the playername
				playerName = player.getName().strip()
				break

		text = ""
		ruleFound = False
		for rule in self.__rules:
			matching = True
			for ruleKeyWord in ruleKeyWords:
				if not ruleKeyWord.lower() in rule.lower():
					matching = False
					break
			if matching:
				text = rule
				ruleFound = True
				break

		if not ruleFound:
			text = " ".join(ruleKeyWords)

		self.warnPlayer(playerName, text, playerIdx)

		return 1


	def onChatMessage(self, playerid, text, channel, flags):
		if text.strip().lower() != "/rules":
			return

		rules = "Rules: " + ", ".join(self.__rules)
		mm_utils.msg_server(rules)


	def init( self ):
		"""Provides default initialisation."""

		# Load the configuration
		self.__config = self.mm.getModuleConfig(configDefaults)
		self.__rules = self.__config["rules"]
		self.__showBold = self.__config["showBold"]
		self.__showOrange = self.__config["showOrange"]
		self.__showEachSeconds = self.__config["showEachSeconds"]
		self.__showOrdered = self.__config["showOrdered"]
		self.__rulePrefix = self.__config["rulePrefix"]
		self.__ruleWarnNewlines = self.__config["ruleWarnNewlines"]
		self.__showRuleWarnBlur = self.__config["showRuleWarnBlur"]
		self.__replaceWelcomeMessageWithRules =  self.__config["replaceWelcomeMessageWithRules"]

		# Settings welcome message
		if self.__replaceWelcomeMessageWithRules:
			host.rcon_invoke("sv.welcomeMessage \"Rules: " + ", ".join(self.__rules) + "\"")

		# Register your game handlers and provide any
		# other dynamic initialisation here
		self.timer = bf2.Timer(self.announce, self.__showEachSeconds, 1, 1)
		self.timer.setRecurring(self.__showEachSeconds)

		if 0 == self.__state:
			# Register your host handlers here
			host.registerHandler("ChatMessage", self.onChatMessage, 1)

		# Register our rcon command handlers
		self.mm.registerRconCmdHandler( 'rules', { 'method': self.cmdExec, 'subcmds': self.__cmds, 'level': 1 } )

		# Update to the running state
		self.__state = 1

	def shutdown( self ):
		"""Shutdown and stop processing."""

		# Unregister game handlers and do any other
		# other actions to ensure your module no longer affects
		# the game in anyway
		self.mm.unregisterRconCmdHandler( 'warn' )

		self.timer.destroy()
		self.timer = None

		# Flag as shutdown as there is currently way to:
		# host.unregisterHandler
		self.__state = 2

	def update( self ):
		"""Process and update.
		Note: This is called VERY often processing in here should
		be kept to an absolute minimum.
		"""
		pass

def mm_load( modManager ):
	"""Creates and returns your object."""
	return Rules( modManager )
