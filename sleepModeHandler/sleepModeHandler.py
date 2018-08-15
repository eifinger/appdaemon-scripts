import appdaemon.plugins.hass.hassapi as hass
import messages
import globals
#
# App which sets the sleep mode on/off
#
# Args:
#   app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#   input_boolean: input_boolean holding the sleepmode. example: input_boolean.sleepmode
#   location_sensors: location sensors of users. example: sensor.location_user_one,sensor.location_user_two
#   room: Room name in which both users must be. example: Wohnzimmer
#   not_home: State of location_sensor indicating someone is not home. example: not_home
#   after: when to start triggering this app. example: 22:00
#   delay: seconds to wait before turning sleepmode on/off. example: 120
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class SleepModeHandler(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args,"app_switch")
        self.location_sensors = globals.get_arg_list(self.args,"location_sensors")
        self.room = globals.get_arg(self.args,"room")
        self.not_home = globals.get_arg(self.args,"not_home")
        self.after = globals.get_arg(self.args,"after")
        self.delay = globals.get_arg(self.args,"delay")
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                self.log("{} changed from {} to {}".format(entity,old,new))
                if new == "on":
                    self.turn_on(self.ishome)
                    self.log("Setting {} to on".format(self.ishome))
                if new == "off":
                    if self.are_others_away(entity):
                        self.turn_off(self.ishome)
                        self.log("Setting {} to off".format(self.ishome))
                        self.call_service("notify/group_notifications",message=messages.isHome_off())

    def are_others_away(self, entity):
        self.log("Entity: {}".format(entity))
        for input_boolean in self.input_booleans:
            self.log("{} is {}".format(input_boolean,self.get_state(input_boolean)))
            if input_boolean == entity:
                pass
            elif self.get_state(input_boolean) == "on":
                self.log("{} is still at on".format(input_boolean))
                return False
        self.log("Everybody not home")
        return True

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
      
