import appdaemon.plugins.hass.hassapi as hass
import random

class TurnEntityOffInXIntent(hass.Hass):

    def initialize(self):
        return

    def getIntentResponse(self, slots, devicename):
        ############################################
        # an Intent to give back the state from a light.
        # but it also can be any other kind of entity
        ############################################           
        try:
            self.log("slots: {}".format(slots))
            entityname = self.args["entities"][slots["device"]]
            duration = [slots["duration"]]
            text = self.random_arg(self.args["textLine"]) + state            
        except:
            text = self.random_arg(self.args["Error"])
        return text

    def floatToStr(self,myfloat):
        ############################################
        # replace . with , for better speech
        ############################################
        floatstr = str(myfloat)
        floatstr = floatstr.replace(".",",")
        return floatstr