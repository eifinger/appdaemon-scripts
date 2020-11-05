import appdaemon.plugins.hass.hassapi as hass
import random


class temperatureStateIntent(hass.Hass):
    def initialize(self):
        """
        Initialize the next callable.

        Args:
            self: (todo): write your description
        """
        return

    def getIntentResponse(self, slots, devicename):
        """
        Gets the response for a device

        Args:
            self: (todo): write your description
            slots: (todo): write your description
            devicename: (str): write your description
        """
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
        """
        Returns float ascii string.

        Args:
            self: (todo): write your description
            myfloat: (todo): write your description
        """
        ############################################
        # replace . with , for better speech
        ############################################
        floatstr = str(myfloat)
        floatstr = floatstr.replace(".", ",")
        return floatstr

    def random_arg(self, argName):
        """
        Return the value from argname.

        Args:
            self: (todo): write your description
            argName: (str): write your description
        """
        ############################################
        # pick a random text from a list
        ############################################
        if isinstance(argName, list):
            text = random.choice(argName)
        else:
            text = argName
        return text
