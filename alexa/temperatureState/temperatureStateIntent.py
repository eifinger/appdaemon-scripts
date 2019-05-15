import appdaemon.plugins.hass.hassapi as hass
import random


class temperatureStateIntent(hass.Hass):
    def initialize(self):
        return

    def getIntentResponse(self, slots, devicename):
        ############################################
        # give temperature for a list of temperature sensors
        ############################################
        try:
            if self.args["language"] == "DE":
                temp = (
                    self.floatToStr(
                        self.get_state(self.args["sensors"][slots["location"]])
                    )
                    + self.args["temperatureUnit"]
                )
            else:
                temp = (
                    str(self.get_state(self.args["sensors"][slots["location"]]))
                    + self.args["temperatureUnit"]
                )
            text = self.random_arg(self.args["textLine"]) + temp
        except:
            text = self.random_arg(self.args["Error"])
        return text

    def floatToStr(self, myfloat):
        ############################################
        # replace . with , for better speech
        ############################################
        floatstr = str(myfloat)
        floatstr = floatstr.replace(".", ",")
        return floatstr

    def random_arg(self, argName):
        ############################################
        # pick a random text from a list
        ############################################
        if isinstance(argName, list):
            text = random.choice(argName)
        else:
            text = argName
        return text
