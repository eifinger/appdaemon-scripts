import appdaemon.plugins.hass.hassapi as hass
import random
import globals


class nextBusIntent(hass.Hass):
    def initialize(self):
        self.sensor = globals.get_arg(self.args, "sensor")
        self.textLine = globals.get_arg(self.args, "textLine")
        self.Error = globals.get_arg(self.args, "Error")

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
            text = self.Error
        return text
