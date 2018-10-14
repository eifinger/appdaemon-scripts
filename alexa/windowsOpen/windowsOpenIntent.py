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
            doors_dict = self.listService.getDoor()
            doors_tilted_dict = self.listService.getDoorTilted()
            window_open_list = []
            door_open_list = []
            door_tilted_list = []
            #iterate over all window entities
            for key, value in windows_dict.items():
                #if a window is open ("on") add it to the window_open_list
                if self.get_state(value) == "on":
                    window_open_list.append(value)
            #iterate over all door entities
            for key, value in doors_dict.items():
                #if a door is open ("on") add it to the door_open_list
                if self.get_state(value) == "on":
                    door_open_list.append(value)
            #iterate over all door_tilted entities
            for key, value in doors_tilted_dict.items():
                #if a door is tilted ("on") add it to the door_tilted_list
                if self.get_state(value) == "on":
                    door_tilted_list.append(value)

            text = ""
            # add open windows to response
            if len(window_open_list) > 0:
                if text != "":
                    text = text + " <break strength=\"weak\"/>"
                text = text + self.args["textLineWindowOpen"]
                for entity in window_open_list:
                    text = text + " <break strength=\"weak\"/>" + self.friendly_name(entity)
            # add open doors to response
            if len(door_open_list) > 0:
                if text != "":
                    text = text + " <break strength=\"weak\"/>"
                text = text + self.args["textLineDoorOpen"]
                for entity in door_open_list:
                    text = text + " <break strength=\"weak\"/>" + self.friendly_name(entity)
            # add tilted doors to reponse
            if len(door_tilted_list) > 0:
                if text != "":
                    text = text + " <break strength=\"weak\"/>"
                text = text + self.args["textLineDoorTilted"]
                for entity in door_tilted_list:
                    friendly_name = self.friendly_name(entity)
                    # remove "gekippt" (german for tilted) from the friendly name
                    friendly_name = friendly_name.replace(" gekippt","")
                    friendly_name = friendly_name.replace(" Gekippt","")
                    text = text + " <break strength=\"weak\"/>" + friendly_name
            # if all closed response
            if text == "":
                text = self.args["textLineClosed"]
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