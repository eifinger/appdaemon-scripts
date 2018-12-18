import appdaemon.plugins.hass.hassapi as hass

class guestInformIntent(hass.Hass):

    def initialize(self):
        return

    def getIntentResponse(self, slots, devicename):
        ############################################
        # an Intent to give back the state from a light.
        # but it also can be any other kind of entity
        ############################################           
        try:
            text = "Das weiß ich leider im Moment nicht"
            self.log("Slots: {}".format(slots))
            dir(self)
            dir(self.entities)
            self.log("Entities: {}".format(self.entities))
        except:
            text = self.random_arg(self.args["Error"])
        return text

    def floatToStr(self, myfloat):
        ############################################
        # replace . with , for better speech
        ############################################
        floatstr = str(myfloat)
        floatstr = floatstr.replace(".",",")
        return floatstr