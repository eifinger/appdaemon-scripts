import appdaemon.plugins.hass.hassapi as hass
import random


class nextBusIntent(hass.Hass):
    def initialize(self):
        self.sensor = self.args["sensor"]
        self.textLine = self.args["textLine"]
        self.error = self.args["error"]

    def getIntentResponse(self, slots, devicename):
        ############################################
        # give next bus departure
        ############################################
        try:
            state = self.get_state(self.sensor, attribute="all")
            line = state["attributes"]["line"]
            minutes = state["attributes"]["minutes"]
            text = self.textLine.format(line, minutes)
        except:
            text = self.error
        return text
