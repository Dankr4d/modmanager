# vim: ts=4 sw=4 noexpandtab
""" MOCKUP
	# Set next map (not forced, wait until map ended)
	RCON: m <n, next> <ti, cq, nv, ..> <size> <map_substr> [<map_substr_2>, <...>]
	# Run map now
	RCON: m <r, run> <ti, cq, nv, ..> <size> <map_substr> [<map_substr_2>, <...>]
"""

# TODO: When maplist is changing at end of round and a map is changed with "m run" command, server is crashing.
#       This maybe will happen with "m next" command too.
# TODO: Map chat command not working when dead
# TODO: Currently we need to add the first maplist into serversettings AND maprotation.ini

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
	"availableMaps": [
		"belgrade",
		"highway_tampa",
		"operation_shingle",
		"suez_canal",
		"bridge_at_remagen",
		"liberation_of_leipzig",
		"port_bavaria",
		"tunis_harbor",
		"camp_gibraltar",
		"minsk",
		"shuhia_taiba",
		"verdun",
		"cerbere_landing",
		"molokai",
		"sidi_power_plant",
		"wake_island_2142",
		"fall_of_berlin",
		"operation_blue_pearl",
		"strike_at_karkand",
		"yellow_knife",
	],
}


class MapRotation( object ):

	def __init__( self, modManager ):
		# ModManager reference
		self.mm = modManager

		# Internal shutdown state
		self.__state = 0

		# Const messages
		self.LESS_THAN_3_PARAMS = "You passed '%i' parameter but, required are at least 3."
		self.SECOND_PARAM_AS_INT = "Second parameter must be an integer (mapsize)"
		self.NO_MAP_FOUND = "No map has been found."
		self.MORE_THAN_ONE_MAP_FOUND = "More than 1 map has been found:\n"
		self.FOUND_MAP_RUN_NOW = "Found map: %s, changing now.."
		self.FOUND_MAP_RUN_NEXT = "Found map: %s, set map to be played as next map."

		# Add any static initialisation here.
		# Note: Handler registration should not be done here
		# but instead in the init() method

		# Your rcon commands go here:
		self.__cmds = {
			'next': { 'method': self.cmdSetNextMap, 'aliases': [ 'n' ], 'level': 10 },
			'run': { 'method': self.cmdSetMap, 'aliases': [ 'r' ], 'level': 10 },
		}


	def readMaps(self, path):
		# TODO: Add checks
		# TODO: Fix os seperator
		result = {}
		for level in self.__availableMaps:
			desc = path + "/" + level + "/" + "info" + "/" + level + ".desc"
			result[level] = {}

			root = minidom.parse(desc)

			for mode in root.getElementsByTagName("modes")[0].getElementsByTagName("mode"):
				gamemode = mode.getAttribute("type").replace("gpm_", "")
				result[level][gamemode] = []
				for maptype in mode.getElementsByTagName("maptype"):
					result[level][gamemode].append(int(maptype.getAttribute("players")))
		return result


	def findMaps(self, gamemode, size, args):
		result = {} # found maps
		for level in self.maps.keys():
			argsMatched = True
			for arg in args:
				if not arg in level.lower():
					argsMatched = False
					break
			if not argsMatched:
				continue
			if not self.maps[level].has_key(gamemode):
				continue
			if not size in self.maps[level][gamemode]:
				continue
			result[level] = self.maps[level]
		return result


	def cmdExec( self, ctx, cmd ):
		"""Execute a MyModule sub command."""

		# Note: The Python doc above is used for help / description
		# messages in rcon if not overriden
		return mm_utils.exec_subcmd( self.mm, self.__cmds, ctx, cmd )


	def getMapRcon(self, ctx, cmd):
		cmdSplit = cmd.split()
		cmdSplitLen = len(cmdSplit)
		if cmdSplitLen < 3:
			ctx.write(self.LESS_THAN_3_PARAMS % cmdSplitLen)
			return (None, None, None)

		gamemode = cmdSplit[0]
		try:
			size = int(cmdSplit[1])
		except ValueError:
			ctx.write(self.SECOND_PARAM_AS_INT)
			return (None, None, None)
		args = cmdSplit[2:]

		foundMaps = self.findMaps(gamemode, size, args)

		if len(foundMaps) == 0:
			ctx.write(self.NO_MAP_FOUND)
			return (None, None, None)
		elif len(foundMaps) > 1:
			ctx.write(self.MORE_THAN_ONE_MAP_FOUND)
			for idx, mapName in enumerate(foundMaps.keys()):
				ctx.write(str(idx + 1) + ": " + mapName + "\n")
				idx += 1
			return (None, None, None)

		mapName = foundMaps.keys()[0]

		return (mapName, gamemode, size)


	def cmdSetMap( self, ctx, cmd ):
		"""Does XYZ.
		Details about this function
		"""

		(mapName, gamemode, size) = self.getMapRcon(ctx, cmd)

		if mapName == None:
			return

		ctx.write(self.FOUND_MAP_RUN_NOW % mapName)
		self.mm.rcon().mapRun(ctx, mapName, "gpm_" + gamemode, size)

		return 1


	def cmdSetNextMap( self, ctx, cmd ):
		"""Does XYZ.
		Details about this function
		"""

		(mapName, gamemode, size) = self.getMapRcon(ctx, cmd)

		if mapName == None:
			return

		ctx.write(self.FOUND_MAP_RUN_NEXT % mapName)
		nextIdx = int(host.rcon_invoke("maplist.currentMap").strip()) + 1
		mapCount = int(host.rcon_invoke("maplist.mapCount").strip())

		if nextIdx == mapCount:
			self.mm.rcon().mapAppend(ctx, mapName, "gpm_" + gamemode, size)
		else:
			self.mm.rcon().mapInsert(ctx, nextIdx, mapName, "gpm_" + gamemode, size)

		return 1


	def maplistLogic(self, playerConnected = False):
		playerCount = len(bf2.playerManager.getPlayers())

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
		# TODO: Be aware about map set next map (e.g. m nv 16 camp)
		if 1 != self.__state:
			return 0
		# Put your actions here
		self.maplistLogic(True)


	def onPlayerDisconnect(self, player):
		"""Update maplist if treshold is reached."""
		# TODO: Be aware about map set next map (e.g. m nv 16 camp)
		if 1 != self.__state:
			return 0
		# Put your actions here
		self.maplistLogic(False)


	def init( self ):
		"""Provides default initialisation."""

		# Load the configuration
		self.__config = self.mm.getModuleConfig( configDefaults )
		self.__maplists = self.__config["maplists"]
		self.__maplistPath = self.__config["maplistPath"]
		self.__availableMaps = self.__config["availableMaps"]
		self.__force = self.__config["force"]
		self.maps = self.readMaps("mods/bf2142/levels")
		# Available maps (including gamemode + size)
		# self.maps format example:
		#		{
		#			"Cerbere_Landing": {
		#				"cq": [16, 32],
		#				"coop": [16],
		#				"nv": [16, 32],
		#				"sp": [16]
		#			},
		#			[...]
		#		}

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
