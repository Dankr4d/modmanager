# vim: ts=4 sw=4 noexpandtab

import bf2
import host
import mm_utils

import ConfigParser
import sys
sys.path.append('../Python-2.3.4/build/lib.linux-x86_64-2.3/')
from xml.dom import minidom


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
__description__ = "Map rotataion v%s" % __version__

# Add all your configuration options here
configDefaults = {
	"maplistPath": "mods/bf2142/settings/",
	"maplists": {
		0: "maplist.con",
	},
	"force": 0,
}


class MapRotation( object ):

	def __init__( self, modManager ):
		# ModManager reference
		self.mm = modManager

		# Internal shutdown state
		self.__state = 0

		# Add any static initialisation here.
		# Note: Handler registration should not be done here
		# but instead in the init() method

		# Your rcon commands go here:
		self.__cmds = {}


	def cmdExec( self, ctx, cmd ):
		"""Execute a MyModule sub command."""

		# Note: The Python doc above is used for help / description
		# messages in rcon if not overriden
		return mm_utils.exec_subcmd( self.mm, self.__cmds, ctx, cmd )


	def maplistLogic(self, playerConnected = False):
		playerCount = 0

		if host.sgl_getIsAIGame():
			for player in bf2.playerManager.getPlayers():
				if not player.isAIPlayer():
					playerCount += 1
		else:
			playerCount = bf2.playerManager.getNumberOfPlayers()

		if not playerConnected:
			playerCount -= 1

		if playerCount in self.__maplists:
			mm_utils.msg_server("New maplist set: " + self.__maplists[playerCount])
			host.rcon_invoke("mapList.configFile " + self.__maplistPath + self.__maplists[playerCount])
			host.rcon_invoke("mapList.load")
			if self.__force or playerCount == 0:
				host.rcon_invoke("admin.runNextLevel")


	def onPlayerConnect(self, player):
		"""Update maplist if treshold is reached."""
		if 1 != self.__state:
			return 0
		if player.isAIPlayer():
			return 0
		self.maplistLogic(True)


	def onPlayerDisconnect(self, player):
		"""Update maplist if treshold is reached."""
		if 1 != self.__state:
			return 0
		if player.isAIPlayer():
			return 0
		self.maplistLogic(False)


	def init( self ):
		"""Provides default initialisation."""

		# Load the configuration
		self.__config = self.mm.getModuleConfig( configDefaults )
		self.__maplists = self.__config["maplists"]
		self.__maplistPath = self.__config["maplistPath"]
		self.__force = self.__config["force"]

		# Register your game handlers and provide any
		# other dynamic initialisation here

		if 0 == self.__state:
			# Register your host handlers here
			host.registerHandler("PlayerConnect", self.onPlayerConnect, 1)
			host.registerHandler("PlayerDisconnect", self.onPlayerDisconnect, 1)

		# Register our rcon command handlers
		# self.mm.registerRconCmdHandler( 'm', { 'method': self.cmdExec, 'subcmds': self.__cmds, 'level': 1 } ) # TODO: Disabled because see comment on top of the file

		# Update to the running state
		self.__state = 1

	def shutdown( self ):
		"""Shutdown and stop processing."""

		# Unregister game handlers and do any other
		# other actions to ensure your module no longer affects
		# the game in anyway
		# self.mm.unregisterRconCmdHandler( 'm' )

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
	return MapRotation( modManager )
