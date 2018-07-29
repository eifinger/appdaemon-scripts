import appdaemon.plugins.hass.hassapi as hass
import random

class lightStateIntent(hass.Hass):

    def initialize(self):
        return

    def getIntentResponse(self, slots, devicename):
        ############################################
        # an Intent to give back the state from a light.
        # but it also can be any other kind of entity
        ############################################           
        try:
            entityname = self.args["entities"][slots["device"]]
            state = self.get_state(entityname)
            if isinstance(state,float):
                if self.args["language"] == "DE":
                    state = self.floatToStr(state)
                else:
                    state = str(state)
            elif isinstance(state,str):
                state = state
            else:
                state = self.args["unreadableState"]
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