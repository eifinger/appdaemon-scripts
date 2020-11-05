import appdaemon.plugins.hass.hassapi as hass

#
# Provide the list of HA entities for Alexa Apps
#
#
# Args:
#
# switchable: dict of switchable entities
# temperature: dict of temperature sensors
# door: dict of reed sensors showing if the door is completely open
# door_tilted: dict of reed sensors showing if a door is partially/leaning open
# window: dict of reed sensors showing if a window is open
#
#
# Release Notes
#
# Version 1.0:
#   Initial Version


class ListService(hass.Hass):
    def initialize(self):
        """
        Initialize the next callable.

        Args:
            self: (todo): write your description
        """
        return

    def getSwitchable(self):
        """
        : return : py : class : rtype : class : return : the current : class : rtype : str

        Args:
            self: (todo): write your description
        """
        return self.args["switchable"]

    def getTemperature(self):
        """
        Gets the current user s }

        Args:
            self: (todo): write your description
        """
        return self.args["temperature"]

    def getDoor(self):
        """
        Return door

        Args:
            self: (todo): write your description
        """
        return self.args["door"]

    def getWindow(self):
        """
        Returns the currently active window

        Args:
            self: (todo): write your description
        """
        return self.args["window"]

    def getDoorTilted(self):
        """
        Return the doorted door door

        Args:
            self: (todo): write your description
        """
        return self.args["door_tilted"]
