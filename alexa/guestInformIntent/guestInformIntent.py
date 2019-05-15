import appdaemon.plugins.hass.hassapi as hass
from fuzzywuzzy import process


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
            if slots["fuzzyword"] is not None and slots["fuzzyword"] is not "":
                tuple_list = process.extract(slots["fuzzyword"], self.get_choices())
                self.log("tuple_list: {}".format(tuple_list))
                entities = [
                    word for (word, confidence) in tuple_list if confidence > 60
                ]
                text = "Du kannst folgende Dinge kontrollieren. {}".format(
                    ", ".join(entities)
                )
        except:
            text = self.random_arg(self.args["Error"])
        return text

    def get_choices(self):
        """
        Get all possible choices from switch / light / group / climate / media_player
        :return:
        """
        list = []
        # Add groups
        for group in dir(self.entities.group):
            if not group.startswith("__"):
                list.append(self.friendly_name("group." + group))
        # Add switch
        for switch in dir(self.entities.switch):
            if not switch.startswith("__"):
                list.append(self.friendly_name("switch." + switch))
        # Add light
        for light in dir(self.entities.light):
            if not light.startswith("__"):
                list.append(self.friendly_name("light." + light))
        # Add climate
        for climate in dir(self.entities.climate):
            if not climate.startswith("__"):
                list.append(self.friendly_name("climate." + climate))
        # Add media_player
        for media_player in dir(self.entities.media_player):
            if not media_player.startswith("__"):
                list.append(self.friendly_name("media_player." + media_player))
        return list

    def floatToStr(self, myfloat):
        ############################################
        # replace . with , for better speech
        ############################################
        floatstr = str(myfloat)
        floatstr = floatstr.replace(".", ",")
        return floatstr
