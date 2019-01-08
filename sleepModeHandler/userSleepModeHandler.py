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
#   duration: seconds to wait before turning sleepmode on/off. example: 120
#
# Release Notes
#
# Version 1.0:
#   Initial Version


class UserSleepModeHandler(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        self.location_sensor = globals.get_arg(self.args, "location_sensor")
        self.room = globals.get_arg(self.args, "room")
        self.duration = globals.get_arg(self.args, "duration")
        self.input_boolean = globals.get_arg(self.args, "input_boolean")

        self.listen_state_handle_list.append(
            self.listen_state(self.state_change, self.location_sensor, duration=self.duration))
    
    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new != old:
                if new == self.room:
                    self.log(
                        "{} is in {} for more than {}s. Turning {} on".format(
                            self.friendly_name(self.location_sensor),
                            self.room,
                            self.duration,
                            self.input_boolean
                        )
                    )
                    self.turn_on(self.input_boolean)
                elif new != self.room:
                    self.log(
                        "{} is outside {} for more than {}s. Turning {} off".format(
                            self.friendly_name(self.location_sensor),
                            self.room,
                            self.duration,
                            self.input_boolean
                        )
                    )
                    self.turn_off(self.input_boolean)

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

