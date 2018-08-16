import appdaemon.plugins.hass.hassapi as hass
import globals
#
# Centralizes messaging. Among other things, it will determine whether a user is at home and if yes in which room. 
# Then Alexa in that room will be used additionally to Telegram
#
# Args:
#  media_player: media player to which alexa is connected. example: media_player.denon_avrx1300w
#  source: media player source of alexa. example: CBL/SAT
#  alexa_media_player: media player entity of alexa to use. example: media_player.kevins_echo_dot_oben
#
# 
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class Notifier(hass.Hass):

    def initialize(self):
        self.media_player = globals.get_arg(self.args,"media_player")
        self.source = globals.get_arg(self.args,"source")
        self.alexa_media_player = globals.get_arg(self.args,"alexa_media_player")

        self.__NOTIFY__ = "notify/"
        self.__ALEXA_TTS__ = "media_player.alexa_tts"

    def notify(self, notify_name, message, useAlexa=True, useTelegram=True):
        if useTelegram:
            self.log("Notifying via Telegram")
            self.call_service(self.__NOTIFY__ + notify_name,message=message)
        if useAlexa:
            self.log(self.get_state(self.media_player, attribute = "all"))
            if self.get_state(self.media_player) == "on":
                if self.get_state(self.media_player, attribute = "all")["attributes"]["source"] == self.source:
                    self.call_service(self.__ALEXA_TTS__, entity=self.alexa_media_player, message=message)


    
    def terminate(self):
        pass

