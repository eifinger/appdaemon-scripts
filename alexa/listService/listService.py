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
        self.args["switchable"]

    def getTemperature(self):
        self.args["temperature"]

    def getDoor(self):
        self.args["door"]

    def getWindow(self):
        self.args["window"]

    def getDoorPartial(self):
        self.args["door_partial"]