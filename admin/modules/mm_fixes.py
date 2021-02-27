# vim: ts=4 sw=4 noexpandtab
"""Fixes module."""

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
	'bf2': False,
	'bf2142': True,
	'bfheroes': False,
	'bfp4f': False
}

# Set the description of your module here
__description__ = "Fixes v%s" % __version__

# Add all your configuration options here
configDefaults = { }


class Fixes( object ):

	def __init__( self, modManager ):
		# ModManager reference
		self.mm = modManager

		# Internal shutdown state
		self.__state = 0


	def onGameStatusChanged( self, status ):
		if status == bf2.GameStatus.PreGame:
			# Fixes that bot's are endless spamming sentry drones.
			# They're disabled for bots.
			host.rcon_invoke("ObjectTemplate.activeSafe GenericFireArm Unl_Drone_Sentry_Detonator")
			host.rcon_invoke("ObjectTemplate.aiTemplate \"\"")


	def init( self ):
		"""Provides default initialisation."""

		# Load the configuration
		self.__config = self.mm.getModuleConfig( configDefaults )

		# Register your game handlers and provide any
		# other dynamic initialisation here

		if 0 == self.__state:
			# Register your host handlers here
			host.registerGameStatusHandler( self.onGameStatusChanged )

		# Update to the running state
		self.__state = 1


	def shutdown( self ):
		"""Shutdown and stop processing."""
		host.unregisterGameStatusHandler( self.onGameStatusChanged )
		self.__state = 2


	def update( self ):
		"""Process and update.
		Note: This is called VERY often processing in here should
		be kept to an absolute minimum.
		"""
		pass


def mm_load( modManager ):
	"""Creates and returns your object."""
	return Fixes( modManager )
