import appdaemon.plugins.hass.hassapi as hass
import globals
#
# Centralizes messaging. Among other things, it will determine whether a user is at home and if yes in which room. 
# Then Alexa in that room will be used additionally to Telegram
#
# Args:
#  app_switch_alexa: mutes alexa. example: 
#  alexa_media_player: media player entity of alexa to use. example: media_player.kevins_echo_dot_oben
#  user_location_sensors: sensors showing the location of users
#  alexa_to_location_mapping: mapping of which alexa device is used for which room
#
# 
#
# Release Notes
#
# Version 1.1:
#   Remove media_player constraints. If connected via bluetooth alexa can always be heard
#
# Version 1.0:
#   Initial Version

class Notifier(hass.Hass):

    def initialize(self):
        self.alexa_media_player = globals.get_arg(self.args,"alexa_media_player")
        self.app_switch_alexa = globals.get_arg(self.args,"app_switch_alexa")
        

        self.__NOTIFY__ = "notify/"
        self.__ALEXA_TTS__ = "media_player/alexa_tts"
        self.__GROUP_NOTIFICATIONS__ = "group_notifications"

    def notify(self, notify_name, message, useAlexa=True, useTelegram=True):
        if useTelegram:
            self.log("Notifying via Telegram")
            self.call_service(self.__NOTIFY__ + notify_name,message=message)
        if useAlexa and self.get_state(self.app_switch_alexa) == "on":
            self.log("Notifying via Alexa")
            self.call_service(self.__ALEXA_TTS__, entity_id=self.alexa_media_player, message=message)

    def getAlexaDeviceForUserLocation(self, notify_name):
        if notify_name == __GROUP_NOTIFICATIONS__:
            return self.args["alexa_to_location_mapping"]["Wohnzimmer"]
        elif notify_name.lower() in  self.args["user_location_sensors"]:
            location = self.get_state(self.args["user_location_sensors"][notify_name.lower()])
            if location in self.args["alexa_to_location_mapping"]:
                return self.args["alexa_to_location_mapping"][location]
            else:
                return None
        else:
            self.log("Unknown notify_name: {}".format(notify_name))
            return None
    
    def terminate(self):
        pass

