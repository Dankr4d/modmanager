# vim: ts=4 sw=4 noexpandtab
"""Admin module."""

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
		2001: "538fcdbc",
		44981: "12341234",
	},
	"msgNotAnAdmin": "Tried to login as admin",
	"msgNameHacks": "Name hacks",
	"chatPrefixes": ["!", "/"],
	"commands": [
		{
			"cmd": "adm",
			"subcmd": "help",
			"chat": ["help", "?"]
		},
		{
			"cmd": "rules",
			"subcmd": "warn",
			"chat": ["warn", "w"]
		},
		{
			"cmd": "adm",
			"subcmd": "kick",
			"chat": ["kick", "k"]
		},
		{
			"cmd": "adm",
			"subcmd": "ban",
			"chat": ["ban", "b"]
		},
		{
			"cmd": "adm",
			"subcmd": "bana",
			"chat": ["bana", "ba"]
		},
		{
			"cmd": "adm",
			"subcmd": "unban",
			"chat": ["unban"]
		},
	],
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
			'help': { 'method': self.cmdHelp, 'level': 10 },
			'kick': { 'method': self.cmdKick, 'args': '<player> <reason>', 'level': 10 },
			'ban': { 'method': self.cmdBanKey, 'args': '<player> <perm|duration> <reason>', 'level': 10 },
			'bana': { 'method': self.cmdBanAddress, 'args': '<player> <perm|duration> <reason>', 'level': 10 },
			'unban': { 'method': self.cmdUnban, 'args': '<player> <reason>', 'level': 10 },
		}


	def findBansByName(self, name):
		result = []
		bans = self.mm.banManager().getBanList()

		for key in bans.keys():
			ban = bans[key]
			if name.lower() in ban["nick"].lower():
				result.append(ban)

		return result


	def cmdExec( self, ctx, cmd ):
		"""Execute an Admin sub command."""

		# Note: The Python doc above is used for help / description
		# messages in rcon if not overriden
		return mm_utils.exec_subcmd( self.mm, self.__cmds, ctx, cmd )


	def cmdHelp(self, ctx, cmd):
		ctx.write("======== CHAT COMMANDS ========\n")
		for command in self.__commands:
			subcmd = self.mm.rcon()._AdminServer__cmds[command["cmd"]]["subcmds"][command["subcmd"]]
			line = ""
			chatcmdLen = len(command["chat"])
			for idx, chatcmd in enumerate(command["chat"]):
				line += chatcmd
				if idx < chatcmdLen - 1:
					line += "|"
			line += " " + subcmd["args"] + ": " + subcmd["desc"] + "\n"
			ctx.write(line)
		ctx.write("================================\n")

	def cmdKick(self, ctx, cmd):
		"""Kick player for one round."""
		# Note: The Python doc above is used for help / description
		# messages in rcon if not overriden

		cmdSplit = cmd.split()
		cmdSplitLen = len(cmdSplit)

		if cmdSplitLen < 2:
			ctx.write("TODO: playername reason")
			return 0

		player = mm_utils.find_player(cmdSplit[0])

		if player == None:
			ctx.write("TODO: player not found")
			return 0

		reason = " ".join(cmdSplit[1:])

		bannedBy = None
		if ctx.player != None:
			bannedByPlayer = bf2.playerManager.getPlayerByIndex(ctx.player)
			bannedBy = bannedByPlayer.getName() + " (" + str(bannedByPlayer.getProfileId()) + ")"

		self.mm.banManager().banPlayer(player, reason + " (round)", "round", mm_utils.KickBanType.rcon, mm_utils.BanMethod.key, bannedBy)

		return 1


	def cmdBanLogic(self, ctx, cmd, banMethod):
		cmdSplit = cmd.split()
		cmdSplitLen = len(cmdSplit)

		if cmdSplitLen < 3:
			ctx.write("TODO: playername reason")
			return 0

		player = mm_utils.find_player(cmdSplit[0])
		period = cmdSplit[1]
		reason = " ".join(cmdSplit[2:])

		bannedBy = None
		if ctx.player != None:
			bannedByPlayer = bf2.playerManager.getPlayerByIndex(ctx.player)
			bannedBy = bannedByPlayer.getName() + " (" + str(bannedByPlayer.getProfileId()) + ")"

		# Permanent ban
		if period == "perm":
			reason += " (permanent)"
			self.mm.banManager().banPlayer(player, reason, period, mm_utils.KickBanType.rcon, banMethod, bannedBy)
			return 1

		# Time based ban
		periodLastChar = period[-1].lower()
		period = mm_utils.get_int(ctx, period[:-1])

		if period == None:
			ctx.write("TODO: period[:-1] is not an int and not perm")
			return 0

		reason += " ("
		reasonSuffix = ""
		if period != 1:
			reasonSuffix = "s"
		reasonSuffix += ")"

		reason += str(period) + " "
		if periodLastChar == 'd': # day(s)
			reason += "day"
			period *= 60*60*24
		elif periodLastChar == 'h': # hour(s)
			reason += "hour"
			period *= 60*60
		elif periodLastChar == 'm': # minute(s)
			reason += "minute"
			period *= 60
		else:
			ctx.write("TODO: unknown perdio not d, h or m")
			return 0
		reason += reasonSuffix

		self.mm.banManager().banPlayer(player, reason, str(period), mm_utils.KickBanType.rcon, banMethod, bannedBy)

		return 1


	def cmdBanKey(self, ctx, cmd):
		"""Ban player key permanent (perm) or for a specific duration (m = minutes, h = hours, d = days)."""
		return self.cmdBanLogic(ctx, cmd, mm_utils.BanMethod.key)


	def cmdBanAddress(self, ctx, cmd):
		"""Ban address permanent (perm) or for a specific duration (m = minutes, h = hours, d = days)."""
		return self.cmdBanLogic(ctx, cmd, mm_utils.BanMethod.address)


	def cmdUnban(self, ctx, cmd):
		"""Unban player."""
		cmdSplit = cmd.split()
		cmdSplitLen = len(cmdSplit)

		if cmdSplitLen < 2:
			self.mm.info("TODO: <playername> <reason>")
			return

		playerName = cmdSplit[0]
		reason = " ".join(cmdSplit[1:])

		bans = self.findBansByName(playerName)
		bansLen = len(bans)

		if bansLen == 0:
			self.mm.info("TODO: No ban found.")
			return
		elif bansLen > 1:
			self.mm.info("TODO: More than one ban found.")
			return

		ban = bans[0]
		banKey = ""

		if ban["method"] == mm_utils.BanMethod.key:
			banKey = ban["cdkeyhash"]
		elif ban["method"] == mm_utils.BanMethod.address:
			banKey = ban["address"]
		else:
			self.mm.info("TODO: Ban method is invalid (it's not a key or address ban).")
			return

		self.mm.banManager().unbanPlayer(banKey, reason)


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
			if str(self.__admins[profileId]) != password:
				# TODO: self.__admins[profileId] can return an integer if it's numeric only.
				#				Don't know why, check this.
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

		player = bf2.playerManager.getPlayerByIndex(playerIdx)
		profileId = player.getProfileId()

		if not profileId in self.__admins.keys():
			return

		if self.mm.getRconContext(playerIdx).authedLevel == 0:
			return # Player not authenticated via rcon

		prefix = ""
		for chatPrefix in self.__chatPrefixes:
			if text.strip().startswith(chatPrefix):
				prefix = chatPrefix
				break

		if prefix == "":
			return

		textSplit = text.strip().split()
		chatCmd = textSplit[0][len(prefix):]

		# Execute rcon command added to commands list
		for command in self.__commands:
			if chatCmd in command["chat"]:
				self.mm.runRconCommand(playerIdx, "%s %s" % (
					command["cmd"] + " " + command["subcmd"],
					text.strip().replace(prefix + chatCmd + " ", "")
				))
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
