import appdaemon.plugins.hass.hassapi as hass
import random
import isodate
import datetime

class WindowsOpenIntent(hass.Hass):

    def initialize(self):
        self.listService = self.get_app("listService")
        return

    def getIntentResponse(self, slots, devicename):
        ############################################
        # an Intent to give back the state of windows
        ############################################           
        try:
            windows_dict = self.listService.getWindow()
            open_list = []
            #iterate over all window entities
            for key, value in windows_dict.items():
                #if a window is open ("on") add it to the open_list
                if self.get_state(value) == "on":
                    open_list.append(value)

            if len(open_list) == 0:
                text = self.args["textLineClosed"]
            else:
                text = self.args["textLineOpen"]
                for entity in open_list:
                    text = text + "<break strength=\"weak\"/>" + self.friendly_name(entity)
        except Exception as e:
            self.log("Exception: {}".format(e))
            self.log("slots: {}".format(slots))
            text = self.random_arg(self.args["Error"])
        return text

    def random_arg(self,argName):
        ############################################
        # pick a random text from a list
        ############################################
        if isinstance(argName,list):
            text = random.choice(argName)
        else:
            text = argName
        return text