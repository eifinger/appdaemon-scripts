import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which sets the sleep mode on/off
#
# Args:
#   app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
#   input_boolean: input_boolean holding the sleepmode. example: input_boolean.sleepmode
#   location_sensor: location sensor of user. example: sensor.location_user_one
#   room: Room name in which both users must be. example: Wohnzimmer
#   asleep_duration: seconds to wait before turning sleepmode on. example: 120
#   awake_duration: seconds to wait before turning sleepmode off. example: 120
#
# Release Notes
#
# Version 1.1:
#   Added asleep_duration and awake_duration instead of duration
#
# Version 1.0:
#   Initial Version


class UserSleepModeHandler(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.location_sensor = globals.get_arg(self.args, "location_sensor")
        self.room = globals.get_arg(self.args, "room")
        self.asleep_duration = globals.get_arg(self.args, "asleep_duration")
        self.awake_duration = globals.get_arg(self.args, "awake_duration")
        self.input_boolean = globals.get_arg(self.args, "input_boolean")

        self.listen_state_handle_list.append(
            self.listen_state(self.asleep, self.location_sensor, new=self.room, duration=self.asleep_duration))
        self.listen_state_handle_list.append(
            self.listen_state(self.awake, self.location_sensor, old=self.room, duration=self.awake_duration))
    
    def asleep(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                self.log(
                    "{} is in {} for more than {}s. Turning {} on".format(
                        self.friendly_name(self.location_sensor),
                        self.room,
                        self.asleep_duration,
                        self.input_boolean
                    )
                )
                self.turn_on(self.input_boolean)

    def awake(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                self.log(
                    "{} is outside {} for more than {}s. Turning {} off".format(
                        self.friendly_name(self.location_sensor),
                        self.room,
                        self.awake_duration,
                        self.input_boolean
                    )
                )
                self.turn_off(self.input_boolean)

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

