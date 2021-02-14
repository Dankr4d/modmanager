# vim: ts=4 sw=4 noexpandtab
"""Sample module.

This is a Sample ModManager module

===== Config =====
 # Sets option 1
 mm_sample.myOption1 1

 # Sets option 2
 mm_sample.myOption2 "hello there"

===== History =====
 v1.3 - 30/08/2006:
 Added supported games

 v1.2 - 13/08/2005:
 Added missing mm.unregisterRconCmdHandler to shutdown

 v1.1 - 29/07/2005:
 Updated API definition

 v1.0 - 01/07/2005:
 Initial version

Copyright (c)2005 Multiplay
Author: Steven 'Killing' Hartland
"""

import bf2
import host
import mm_utils

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
__description__ = "Admin v%s" % __version__


# Add all your configuration options here
configDefaults = {
	"admins": {
		2001: "538fcdbc"
	},
	"msgNotAnAdmin": "Tried to login as admin",
	"msgNameHacks": "Name hacks",
	"chatPrefixes": ["!", "/"],
	"commands": [
		{
			"cmd": "rules",
			"subcmd": "warn",
			"chat": ["warn", "w"]
		},
		{
			"cmd": "bm",
			"subcmd": "banPlayer",
			"chat": ["ban"]
		},
		{
			"cmd": "bm",
			"subcmd": "removeBan",
			"chat": ["unban"]
		},
		# {
		# 	"cmd": "bm",
		# 	"subcmd": "listBans",
		# 	"chat": ["banlist"]
		# },
		{
			"cmd": "adm",
			"subcmd": "kick",
			"chat": ["kick", "k"]
		},
	],
	# "admins": {
	# 	"pid": 0,
	# 	"name": "",
	# 	"rights": [],
	# }
}

class Admin( object ):

	def __init__( self, modManager ):
		# ModManager reference
		self.mm = modManager

		# Internal shutdown state
		self.__state = 0

		# Add any static initialisation here.
		# Note: Handler registration should not be done here
		# but instead in the init() method

		# Your rcon commands go here:
		self.__cmds = {
			'kick': { 'method': self.cmdKick, 'level': 10 }
		}

	def cmdExec( self, ctx, cmd ):
		"""Execute a MyModule sub command."""

		# Note: The Python doc above is used for help / description
		# messages in rcon if not overriden
		return mm_utils.exec_subcmd( self.mm, self.__cmds, ctx, cmd )

	def cmdKick(self, ctx, cmd):
		"""Kick a player"""
		# Note: The Python doc above is used for help / description
		# messages in rcon if not overriden

		### TODO: Following logic is redundant (copied from mm_rules module)
		cmdSplit = cmd.split()
		cmdSplitLen = len(cmdSplit)

		playerName = cmdSplit[0]
		reason = "Unknown"
		if cmdSplitLen > 1:
			reason = " ".join(cmdSplit[1:])
		player = None
		for playerTmp in bf2.playerManager.getPlayers():
			if playerName.lower() in playerTmp.getName().lower():
				player = playerTmp
				break
		##
		if player == None:
			return

		self.mm.banManager().banPlayer(player, "Kicked for this round (" + reason + ")", "round")
		# kickPlayer( self, player, kickReason=None, kickDelay=None, kickType=mm_utils.KickBanType.rcon )

		return 1

	def onPlayerConnect(self, player):
		"""Do something when a player connect."""
		if 1 != self.__state:
			return 0

		playerName = player.getName()
		profileId = player.getProfileId()

		if profileId in self.__admins.keys():
			# Validate name hack password
			pos1 = playerName.lower().find("|c")
			if pos1 == -1:
				self.mm.banManager().kickPlayer(player, self.__msgNotAnAdmin)
				return
			pos2 = playerName.lower().find("|c", pos1 + 6)
			if pos2 == -1:
				self.mm.banManager().kickPlayer(player, self.__msgNotAnAdmin)
				return
			password = playerName[pos1 + 2:pos1 + 6] + playerName[pos2 + 2:pos2 + 6]
			if self.__admins[profileId] != password:
				self.mm.banManager().kickPlayer(player, self.__msgNotAnAdmin)
				return

			containNameHack = True
			while containNameHack:
				containNameHack = False
				if "|c" in playerName.lower():
					pos = playerName.lower().find("|c")
					containNameHack = True
					playerName = playerName[:pos] + playerName[pos + 6:]
				if "§2" in playerName:
					pos = playerName.find("§2")
					playerName = playerName[:pos] + playerName[pos + 3:] # TODO: Why pos + 3 and not pos + 2?
					containNameHack = True
				if "§3" in playerName:
					pos = playerName.find("§3")
					playerName = playerName[:pos] + playerName[pos + 3:] # TODO: Why pos + 3 and not pos + 2?
					containNameHack = True
		else:
			pattern = ["|c", "§2", "§3"]
			for patter in pattern:
				if patter in playerName.lower():
					self.mm.banManager().kickPlayer(player, self.__msgNameHacks)
		player.setName(playerName.strip())


	def onChatMessage(self, playerIdx, text, channel, flags):
		if playerIdx == -1:
			return

		if text == "/help":
			self.mm.info("IN HELP")
			for command in self.__commands:
				subcmd = self.mm.rcon()._AdminServer__cmds[command["cmd"]]["subcmds"][command["subcmd"]]
				# self.mm.info(repr(command))
				# self.mm.info(repr(subcmd))
				line = ""
				chatcmdLen = len(command["chat"])
				for idx, chatcmd in enumerate(command["chat"]):
					line += chatcmd
					if idx < chatcmdLen - 1:
						line += "|"
				line += " " + subcmd["args"] + ": " + subcmd["desc"]
				host.sgl_sendTextMessage(0, 12, 2, line, 0)

				# mm_utils.msg_server(line)
			return

		player = bf2.playerManager.getPlayerByIndex(playerIdx)
		self.mm.info(repr(player))
		profileId = player.getProfileId()
		self.mm.info(repr(profileId))

		if not profileId in self.__admins.keys():
			self.mm.info("Player is not an admin!")
			return

		isCommand = False
		prefix = ""
		for chatPrefix in self.__chatPrefixes:
			if text.strip().startswith(chatPrefix):
				isCommand = True
				prefix = chatPrefix
				self.mm.info("Found chatprefix: " + prefix)

		if not isCommand:
			self.mm.info("Normal text message, no command!")


		for command in self.__commands:
			textSplit = text.strip().split()
			cmdStr = textSplit[0][len(prefix):]

			self.mm.info(repr(command))
			self.mm.info("'" + cmdStr + "'")
			self.mm.info(repr(command["chat"]))
			# self.mm.info(repr(command.chat))

			if cmdStr in command["chat"]:
				self.mm.info("Found command")
				self.mm.info(repr(self.mm.rcon()._AdminServer__cmds[command["cmd"]]["subcmds"][command["subcmd"]]["method"]))
				self.mm.info(repr(self.mm.rcon().getContext(playerIdx)))
				self.mm.info(repr(text.replace(prefix, "").strip()))
				self.mm.rcon()._AdminServer__cmds[command["cmd"]]["subcmds"][command["subcmd"]]["method"](
					self.mm.rcon().getContext(playerIdx),
					text.strip().replace(prefix + cmdStr, "")
				)
				break


	def init( self ):
		"""Provides default initialisation."""

		# Load the configuration
		self.__config = self.mm.getModuleConfig( configDefaults )
		self.__admins = self.__config["admins"]
		self.__msgNotAnAdmin = self.__config["msgNotAnAdmin"]
		self.__msgNameHacks = self.__config["msgNameHacks"]
		self.__chatPrefixes = self.__config["chatPrefixes"]
		self.__commands = self.__config["commands"]

		# Register your game handlers and provide any
		# other dynamic initialisation here

		if 0 == self.__state:
			# Register your host handlers here
			host.registerHandler("PlayerConnect", self.onPlayerConnect, 1)
			host.registerHandler("ChatMessage", self.onChatMessage, 1)

		# Register our rcon command handlers
		self.mm.registerRconCmdHandler( 'adm', { 'method': self.cmdExec, 'subcmds': self.__cmds, 'level': 1 } )

		# Update to the running state
		self.__state = 1

	def shutdown( self ):
		"""Shutdown and stop processing."""

		# Unregister game handlers and do any other
		# other actions to ensure your module no longer affects
		# the game in anyway
		self.mm.unregisterRconCmdHandler( 'sample' )

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
	return Admin( modManager )
