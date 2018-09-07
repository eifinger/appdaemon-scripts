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
# door_partial: dict of reed sensors showing if a door is partially/leaning open
# window: dict of reed sensors showing if a window is open
# 
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class ListService(hass.Hass):

    def initialize(self):
        return
    
    def getSwitchable(self):
        return self.args["switchable"]

    def getTemperature(self):
        return self.args["temperature"]

    def getDoor(self):
        return self.args["door"]

    def getWindow(self):
        return self.args["window"]

    def getDoorPartial(self):
        return self.args["door_partial"]