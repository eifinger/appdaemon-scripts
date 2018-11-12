import appdaemon.plugins.hass.hassapi as hass
import datetime
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
# Version 1.2.1:
#   Fix: Enqueue alexa messages
#
# Version 1.2:
#   Enqueue alexa messages
#
# Version 1.1:
#   Remove media_player constraints. If connected via bluetooth alexa can always be heard
#
# Version 1.0:
#   Initial Version

__GROUP_NOTIFICATIONS__ = "group_notifications"
__ALEXA_TTS__ = "media_player/alexa_tts"
__NOTIFY__ = "notify/"
__WAIT_TIME__ = 3 # seconds

class Notifier(hass.Hass):

    def initialize(self):
        self.timer_handle_list = []

        self.alexa_media_player = globals.get_arg(self.args,"alexa_media_player")
        self.app_switch_alexa = globals.get_arg(self.args,"app_switch_alexa")

        self.last_alexa_notification_time = None
    

    def notify(self, notify_name, message, useAlexa=True, useTelegram=True):
        if useTelegram:
            self.log("Notifying via Telegram")
            self.call_service(__NOTIFY__ + notify_name,message=message)
        if useAlexa and self.get_state(self.app_switch_alexa) == "on":
            self.log("Notifying via Alexa")
            # check last message
            if self.last_alexa_notification_time != None and (datetime.datetime.now() - self.last_alexa_notification_time < datetime.timedelta(seconds=__WAIT_TIME__)):
                self.timer_handle_list.append(self.run_in(self.notify_callback, __WAIT_TIME__, message=message))
            else:
                self.last_alexa_notification_time = datetime.datetime.now()
                self.call_service(__ALEXA_TTS__, entity_id=self.alexa_media_player, message=message)


    def notify_callback(self, kwargs):
        self.last_alexa_notification_time = datetime.datetime.now()
        self.call_service(__ALEXA_TTS__, entity_id=self.alexa_media_player, message=kwargs["message"])


    def getAlexaDeviceForUserLocation(self, notify_name):
        if notify_name == __GROUP_NOTIFICATIONS__:
            return self.args["alexa_to_location_mapping"]["Wohnzimmer"]
        elif notify_name.lower() in self.args["user_location_sensors"]:
            location = self.get_state(self.args["user_location_sensors"][notify_name.lower()])
            if location in self.args["alexa_to_location_mapping"]:
                return self.args["alexa_to_location_mapping"][location]
            else:
                return None
        else:
            self.log("Unknown notify_name: {}".format(notify_name))
            return None


    def terminate(self):
        for timer_handle in self.timer_handle_list:
            self.cancel_timer(timer_handle)
